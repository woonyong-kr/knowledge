---
title: I·O Bridge 완전 해부 — IMC·PCH·PCIe TLP 와 DMA·MMIO·IRQ
category: 네트워크
keyword: IO Bridge와 NIC
created: 2026-04-20
updated: 2026-04-20
tags: [io-bridge, imc, pch, pcie, tlp, mmio, dma, msi-x, napi, iommu]
summary: CSAPP 가 말하는 I·O Bridge 의 실제 정체(IMC·PCIe Root Complex·PCH) 와 세 종류의 주소 공간, PCIe TLP, 커널의 DMA·MMIO·IRQ API 가 실제 `write` 한 번에 어떻게 엮이는지 추적합니다.
source: _krafton/SW_AI-W08-SQL/docs/team/woonyong-kr/q10-io-bridge.md
---

## Northbridge·Southbridge 에서 IMC·PCH 로

CSAPP 시절(2000 년대 초반) 의 구조는 다음과 같았습니다.

```text
[CPU] ── Front-Side Bus (FSB) ── [Northbridge]
                                    │
                            ┌───────┼────────────┐
                         [DRAM]  [AGP/GPU]   Hub Interface
                                                 │
                                           [Southbridge]
                                                 │
                                    ┌────┬──────┼──────┬─────┐
                                  [PCI][USB][SATA][LAN][Audio]
```

Northbridge 가 CPU 와 고속 장치(메모리·GPU) 를 잇고 메모리 컨트롤러(IMC) 가 여기에 있었습니다. Southbridge 는 저속 I·O(USB, SATA, LAN, Audio, BIOS) 를 담당했고, 둘은 Hub Interface 로 연결됐습니다. CSAPP 가 한 줄로 그린 "I·O Bridge" 는 이 둘을 묶어 추상화한 표현입니다.

현대(Sandy Bridge 2011 이후) 의 구조는 다음과 같습니다.

```text
[CPU 패키지]
  ├─ Core 0 ─┐
  ├─ Core 1 ─┤   LLC (L3) 공유
  ├─ Core 2 ─┤
  ├─ Core 3 ─┘
  │
  ├─ IMC (통합 메모리 컨트롤러) ── DDR 채널 ── [DRAM]
  ├─ PCIe Root Complex ── PCIe 슬롯 ── [GPU / NVMe / 고속 NIC]
  └─ DMI Link ── [PCH (Platform Controller Hub)]
                   ├─ USB, SATA, 저속 Ethernet, Audio, BIOS SPI
```

Northbridge 기능 대부분이 CPU 다이 안으로 들어오면서(IMC, PCIe Root Complex), Southbridge 의 계승자는 PCH 가 됐습니다. CPU 와 PCH 는 DMI 링크(PCIe x4 상당) 로 연결됩니다. 고속 장치는 CPU 와 직결되고, 저속 I·O 는 PCH 를 경유합니다. 그래서 "CPU ↔ DRAM 은 직결" 이 맞고, NIC 은 IMC 가 아니라 PCIe Root Complex 를 거칩니다. "I·O Bridge" 의 핵심 후손이 바로 PCIe Root Complex + PCH 입니다.

## 세 가지 주소 공간

CPU 가 `mov [0x...], rax` 를 때릴 때 주소가 어디로 가는지는 값에 따라 다릅니다.

```text
주소 공간            목적지                        캐싱          접근 명령
물리 DRAM 주소        IMC -> DDR -> DRAM             WB           mov
MMIO 주소            PCIe Root Complex -> 장치 레지스터  UC / WC       mov + UC 매핑
Port I·O 주소         LPC/PCH 의 포트 버스              캐싱 없음      in / out
```

페이지 테이블은 `_PAGE_BIT_PWT`, `_PAGE_BIT_PCD` 비트와 PAT·MTRR 테이블을 조합해 메모리 타입(WB, WT, UC, UC-, WC, WP) 을 결정합니다. `PAGE_KERNEL` 은 WB 이고, `PAGE_KERNEL_NOCACHE` 는 UC, `PAGE_KERNEL_WC` 는 WC 입니다.

MMIO 가 non-cacheable 이어야 하는 이유는 분명합니다. NIC 레지스터 값은 장치 상태에 따라 시시각각 바뀌는데, CPU 캐시에 올려놓으면 옛날 값을 읽게 되고, 쓸 때도 캐시에만 머물면 장치에 명령이 전달되지 않습니다. UC 로 매핑해 매 접근이 실제 PCIe 트랜잭션으로 나가도록 합니다.

PCIe 카드는 BAR(Base Address Register) 에 자신의 MMIO 물리주소 범위를 선언하고, 커널은 이를 읽어 `pci_iomap` → `ioremap` 으로 커널 가상주소에 UC 매핑합니다. `__iomem` 표식은 sparse 정적 분석기가 "이 포인터는 MMIO. 직접 역참조 금지, `readl`·`writel` 만 허용" 을 강제하기 위한 것입니다.

## PCIe 프로토콜 — TLP

PCIe 는 패킷 교환망입니다. CPU ↔ 장치의 모든 트래픽이 TLP(Transaction Layer Packet) 로 오갑니다.

```text
PCIe 스택
  ┌──────────────────────────────┐
  │ Transaction Layer (TLP)      │  "누가 누구에게 뭘"
  ├──────────────────────────────┤
  │ Data Link Layer (DLLP)       │  ACK·NAK, credit
  ├──────────────────────────────┤
  │ Physical Layer               │  Serdes, 레인, 128b/130b 인코딩
  └──────────────────────────────┘
```

TLP 종류는 다음과 같습니다.

```text
Memory Read  (MRd)   CPU 가 MMIO 읽음 / 장치가 DMA 읽음
Memory Write (MWr)   CPU 가 MMIO 씀   / 장치가 DMA 씀
I·O Rd/Wr           레거시 (거의 안 씀)
Config Rd/Wr        BAR, 벤더 ID 등 PCIe config 공간
Message (Msg)       인터럽트(MSI·MSI-X), PME
Completion (Cpl)    읽기 응답
```

Memory Write 는 posted(응답 없음), Memory Read 는 non-posted 라 Completion TLP 로 데이터가 돌아옵니다. Tag 는 여러 개의 outstanding read 를 구분하고, Requester ID(`Bus:Device:Function`) 는 IOMMU 가 장치별 주소 변환 테이블을 찾을 때 사용합니다.

BAR 에 MMIO 가 할당되는 과정은 다음과 같습니다.

```text
[1] BIOS/펌웨어 POST
     └ 각 PCIe 장치에 Config Write 로 BAR0 에 0xFFFFFFFF 쓰기
     └ Config Read 로 다시 읽어 하위 비트를 보면 필요한 크기
     └ 시스템 MMIO 공간에 연속 영역 할당
     └ Config Write 로 BAR0 에 "너의 MMIO 시작주소 = 0xFEBE0000" 기록

[2] OS 부팅 후
     └ pci_resource_start(pdev, 0) 로 값 조회
     └ ioremap 으로 커널 가상주소에 UC 매핑
     └ writel / readl 로 접근
```

## DMA 메커니즘

DMA 의 효용은 비교하면 선명합니다.

```text
[DMA 없이]
  CPU: for (i=0; i<149; i++) writel(skb[i], NIC_DATA_REG);
       -> 149번의 PCIe MWr TLP, 매번 CPU 가 직접

[DMA 로]
  CPU: writel(phys(skb), NIC_TX_DESC_ADDR);
       writel(149, NIC_TX_LEN);
       wmb();
       writel(GO, NIC_DOORBELL);
  NIC: MRd TLP 로 DRAM(phys(skb)) 에서 149B 끌어옴
       -> CPU 는 그 사이 다른 일
```

커널 DMA API 는 두 가지입니다.

- Coherent DMA(`dma_alloc_coherent`): 영속 구조(descriptor ring) 용. 항상 CPU ↔ 장치가 같은 값을 보고 캐싱되지 않아 느리지만 양쪽이 자주 오가는 구조에 적합합니다.
- Streaming DMA(`dma_map_single`): 일회성(`skb` 데이터) 용. 캐싱되지만 map·unmap 호출로 캐시 flush·invalidate 를 명시해야 합니다. 큰 페이로드에 적합합니다.

x86 은 DMA 가 캐시 시스템을 snoop 하므로 명시적 flush 가 거의 필요 없습니다. ARM·MIPS 계열은 snoop 이 약해 소프트웨어로 flush 해야 하고, Linux `arch_sync_dma_for_device` 가 이 차이를 흡수합니다.

IOMMU 는 장치별 가상 주소 공간을 제공합니다. Requester ID(BDF) 로 컨텍스트 테이블을 선택하고 IOTLB 로 페이지 테이블을 캐싱합니다. VM(VT-d) 에서 게스트가 NIC 에 직접 붙는 구조의 기반이며, 잘못된 장치가 엉뚱한 메모리에 DMA 하는 것을 막는 보안 장치이기도 합니다.

## MMIO 와 메모리 배리어

x86 CPU 는 store buffer 가 있어 연속된 write 가 순서대로 버스로 나간다는 보장이 약합니다. NIC 드라이버는 배리어를 명시해야 합니다.

```c
// 잘못된 예
writel(buf_phys, TX_DESC_ADDR);
writel(GO,       DOORBELL);
// store buffer 가 순서를 뒤집으면 NIC 이 아직 안 쓴 descriptor 를 DMA 함

// 올바른 예
writel(buf_phys, TX_DESC_ADDR);
wmb();   // write memory barrier
writel(GO, DOORBELL);
```

리눅스 배리어 종류는 `mb`·`wmb`·`rmb`(전체·쓰기·읽기), `smp_*`(SMP 간에만), `dma_wmb`·`dma_rmb`(DMA 전용, ARM 에서 가벼움) 가 있습니다.

## 인터럽트 — INTx, MSI, MSI-X

Legacy INTx 는 물리 와이어(A·B·C·D) 를 공유하기 때문에 ISR 마다 "누가 쏜 건지" 확인해야 합니다.

MSI 는 인터럽트를 PCIe Memory Write TLP 로 재정의합니다. 장치가 미리 설정된 주소(`0xFEExxxxx`) 에 미리 설정된 데이터(벡터 번호) 를 쓰면 LAPIC 이 받아 CPU 를 깨웁니다.

MSI-X 는 장치당 최대 2048 개 벡터를 할당할 수 있어, 멀티큐 NIC 이 RX 큐마다 MSI-X 벡터 1 개를 할당하고 큐별로 다른 CPU 코어에 분산(RSS, Receive Side Scaling) 할 수 있습니다.

인터럽트 핸들러가 바로 패킷을 처리하지 않고 NAPI 로 넘기는 이유는 초당 수십만~수백만 패킷 상황에서 인터럽트 수가 CPU 를 죽일 수 있기 때문입니다. NAPI 는 인터럽트 한 번 받으면 폴링 모드로 바꿔 큐가 빌 때까지 처리하고, 하드 IRQ 빈도를 급감시킵니다.

## write 한 번이 PCIe TLP 까지 가는 길

`write(sockfd, buf, 149)` 가 선로에 전기신호로 나가기까지의 경로입니다.

```text
[1] user: write(sockfd, buf, 149)  -> syscall 트랩 -> 커널 CPL0

[2] 커널 TCP:
      sock_write_iter -> tcp_sendmsg
      └ kmem_cache_alloc(skbuff_head_cache)  // 224B 메타
      └ page_frag_alloc(149B)                 // 데이터 영역
      └ copy_from_user(skb->data, buf, 149)   // CPU 복사

[3] TCP·IP:
      tcp_transmit_skb -> ip_queue_xmit -> dev_queue_xmit
      └ qdisc enqueue -> __qdisc_run

[4] 드라이버 ndo_start_xmit:
      dma_addr = dma_map_single(dev, skb->data, 149, DMA_TO_DEVICE);
      desc[tail] = { buffer_addr=dma_addr, length=149, cmd=EOP|RS };
      wmb();
      writel(tail, hw_addr + TDT);    // doorbell

[5] PCIe Memory Write TLP (CPU -> NIC)
      Address = BAR_0 + TDT offset
      Payload = tail
      -> PCIe Root Complex -> NIC

[6] NIC:
      doorbell 감지 -> TX DMA 시작
      Memory Read TLP(Address=dma_addr, Length=149)
      -> Root Complex -> IMC -> DRAM
      -> Completion TLP(CplD) 로 149B 데이터 수신
      -> NIC 내부 FIFO SRAM 에 저장

[7] NIC MAC 컨트롤러:
      프리앰블 7B + SFD 1B 앞에 붙임, 뒤에 FCS 4B 계산 추가
      PHY 에 비트 스트림 전달

[8] PHY -> Serdes -> RJ-45 -> 케이블

[9] TX 완료:
      NIC 이 MWr TLP 로 descriptor status 를 DRAM 에 writeback
      MSI-X Msg TLP 로 인터럽트 전달
      LAPIC -> CPU -> intr_msix_tx -> napi_schedule
      NAPI poll 에서 dma_unmap_single + dev_kfree_skb
```

세 가지 흐름을 눈여겨볼 만합니다. CPU 는 데이터 본체를 만지지 않고 유저 → 커널 복사 한 번만 담당합니다. doorbell 도 MMIO write TLP 이고, 인터럽트도 MMIO write TLP 입니다(장치가 LAPIC 의 특정 주소에 값을 씀). 즉 PCIe 위에서는 "명령·데이터·인터럽트" 모두가 같은 패킷 종류로 흐릅니다.

## 성능과 경합

이론 대역폭 비교입니다.

```text
DDR4-3200 (듀얼채널)      약 50 GB/s
PCIe 4.0 x16             약 32 GB/s
PCIe 4.0 x4  (NVMe 하나)  약  8 GB/s
DMI 4.0                  약  8 GB/s  (PCH 경유 총량)
10Gbps NIC               약 1.25 GB/s
100Gbps NIC              약 12 GB/s
```

운영 상 관찰 포인트는 네 가지입니다.

- NUMA: 듀얼 소켓 서버에서 NIC 이 한 CPU 의 PCIe 에 붙어 있으면 반대쪽 CPU 접근 시 UPI 홉 비용이 발생합니다. `irqbalance`, `taskset`, `set_mempolicy` 로 친화성을 조정합니다.
- Cache line ping-pong: descriptor 를 여러 CPU 가 공유하면 캐시 라인이 코어 사이를 오갑니다. 멀티큐 NIC 는 큐별로 코어를 고정합니다(RSS + IRQ affinity).
- Zerocopy: `sendfile(2)`, `splice(2)`, `MSG_ZEROCOPY`, `io_uring` 으로 유저 ↔ 커널 복사를 제거하면 10G 이상에서 체감이 큽니다.
- Interrupt coalescing: NIC 펌웨어가 "N 개 또는 K μs 마다 한 번씩" IRQ 를 묶어서 쏩니다. `ethtool -c eth0` 로 조회·조정합니다.

## 계층 되짚기

하나의 `write()` 호출이 실제로 타고 내려가는 소프트웨어·하드웨어 계층입니다.

```text
하드웨어
  [NIC PCIe 카드]  ── TLP ──  [PCIe Root Complex]  ──  [CPU 다이: IMC / core / cache]

커널 드라이버
  drivers/net/ethernet/...        <- ndo_start_xmit, IRQ 핸들러
  kernel/dma/, linux/dma-mapping  <- DMA API
  arch/x86/kernel/pci-*           <- PCI·PCIe 설정

네트워크 스택
  net/core, net/ipv4              <- skb, qdisc, TCP·IP

시스템콜
  net/socket.c                    <- sock_write_iter

유저공간
  write(sockfd, buf, len)
```

CSAPP 6·10·11 장의 분절된 주제가 이 한 그림에서 한 줄로 이어집니다.
