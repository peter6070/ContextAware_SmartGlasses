// 로컬 표준 입출력으로만 요청을 받는 Matter 컨트롤러 시제품입니다.
import { createInterface } from 'node:readline';
import { resolve } from 'node:path';
import { Environment, Logger, LogLevel } from '@matter/main';
import { ControllerBehavior, ServerNode } from '@matter/main';
import { FabricAuthority } from '@matter/main/protocol';
import { OnOffClient } from '@matter/main/behaviors/on-off';
import { GeneralCommissioning } from '@matter/main/clusters';
import '@matter/nodejs-ble';

// 설정 코드·네트워크 정보가 SDK 진단 로그에 출력되지 않도록 합니다.
Logger.level = LogLevel.FATAL;
const env = Environment.default;
env.vars.set('ble.enable', true);
env.vars.set('storage.path', resolve(process.env.LOCALAPPDATA || process.env.HOME || '.', 'SmartGlassesMatter'));
let controller;

async function init() {
  controller = await ServerNode.create(ServerNode.RootEndpointWithoutGroupcast.with(ControllerBehavior), {
    environment: env, id: 'smart-glasses', commissioning: { enabled: false },
    controller: { adminFabricLabel: 'Smart Glasses' },
  });
  const authority = await controller.env.load(FabricAuthority);
  await authority.defaultFabric({ adminFabricLabel: 'Smart Glasses' });
  await controller.start();
}

function peerList() {
  return [...controller.peers.commissioned].map(p => ({ id: p.id, connected: p.lifecycle.isConnected }));
}

async function execute(request) {
  if (request.op === 'list') return { devices: peerList() };
  if (request.op === 'commission') {
    if (!/^\d{11,21}$/.test(request.code || '') || !request.ssid || typeof request.password !== 'string') {
      throw new Error('등록 코드와 Wi-Fi 정보를 확인하세요.');
    }
    const peer = await controller.peers.commission({
      pairingCode: request.code,
      discoveryCapabilities: { ble: true, onIpNetwork: true },
      wifiNetwork: { wifiSsid: request.ssid, wifiCredentials: request.password },
      regulatoryLocation: GeneralCommissioning.RegulatoryLocationType.IndoorOutdoor,
      regulatoryCountryCode: 'KR',
      onAttestationFailure: findings => findings.every(f => f.level !== 'error'),
    });
    return { id: peer.id };
  }
  if (!['status', 'on', 'off'].includes(request.op)) throw new Error('지원하지 않는 요청입니다.');
  const peer = [...controller.peers.commissioned].find(p => p.id === request.id);
  if (!peer || !peer.lifecycle.isConnected || !peer.lifecycle.isSeeded) throw new Error('장치가 연결되지 않았거나 아직 준비되지 않았습니다.');
  const candidates = [...peer.endpoints].filter(endpoint => endpoint.behaviors.has(OnOffClient));
  if (candidates.length !== 1) throw new Error('On/Off 엔드포인트가 하나가 아닙니다. 장치 설정 확인이 필요합니다.');
  const endpoint = candidates[0];
  if (request.op === 'on') await endpoint.commandsOf(OnOffClient).on();
  if (request.op === 'off') await endpoint.commandsOf(OnOffClient).off();
  // 로컬 캐시는 구독 시점의 값이므로 명령 성공과 실제 상태를 혼동하지 않습니다.
  const state = endpoint.stateOf(OnOffClient).onOff;
  return { endpoint: endpoint.number, cachedState: state, confirmed: false };
}

try {
  await init();
  console.log(JSON.stringify({ ready: true }));
  const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of lines) {
    try {
      const request = JSON.parse(line);
      const result = await execute(request);
      console.log(JSON.stringify({ ok: true, result }));
    } catch (error) {
      // SDK 예외에는 인증 정보가 포함될 수 있어 원문을 출력하지 않습니다.
      console.log(JSON.stringify({ ok: false, error: 'Matter 요청 실패. 기기 연결과 설정을 확인하세요.' }));
    }
  }
} catch (error) {
  console.error('Matter 컨트롤러 초기화 실패. Node.js, Bluetooth 및 네트워크 환경을 확인하세요.');
  process.exitCode = 1;
} finally {
  if (controller) await controller.close();
}
