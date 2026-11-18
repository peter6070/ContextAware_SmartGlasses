// 로컬 표준 입출력으로만 요청을 받는 Matter 컨트롤러 시제품입니다.
import { createInterface } from 'node:readline';
import { resolve } from 'node:path';
import { Environment, Logger, LogLevel, Seconds } from '@matter/main';
import { ControllerBehavior, ServerNode } from '@matter/main';
import { FabricAuthority } from '@matter/main/protocol';
import { OnOffClient } from '@matter/main/behaviors/on-off';
import { GeneralCommissioning } from '@matter/main/clusters';
import { ManualPairingCodeCodec } from '@matter/main/types';
import '@matter/nodejs-ble';
import { safeMatterError } from './errors.mjs';

// SDK 원문 대신 알려진 단계에 대한 고정 문구만 표준 출력으로 보냅니다.
Logger.level = LogLevel.FATAL;
const commissioningStages = new Map([
  ['GetInitialData', '보안 등록 연결 성립. 기기 정보 확인 중'],
  ['OperationalCredentials.DeviceAttestation', 'Matter 기기 인증 중'],
  ['NetworkCommissioning.Wifi', '플러그에 Wi-Fi 정보를 전달하고 연결 확인 중'],
  ['Reconnect', '로컬 IP 네트워크에서 플러그에 다시 연결 중'],
  ['GeneralCommissioning.Complete', 'Matter 등록 마무리 중'],
]);
let commissioning = false;
Logger.facilityLevels = { ControllerCommissioner: LogLevel.INFO };
Logger.destinations.default.write = (text) => {
  if (!commissioning) return;
  const step = text.match(/Executing commissioning step \d+\.\d+: ([\w.]+)/)?.[1];
  const message = commissioningStages.get(step);
  if (message) console.log(JSON.stringify({ progress: message }));
};
const env = Environment.default;
env.vars.set('ble.enable', true);
env.vars.set('storage.path', resolve(process.env.LOCALAPPDATA || process.env.HOME || '.', 'SmartGlassesMatter'));
let controller;
class InvalidRegistrationError extends Error {}
class DeviceNotReadyError extends Error {}
class OnOffEndpointError extends Error {}

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
    if (typeof request.code !== 'string' || !/^(\d{11}|\d{21})$/.test(request.code) ||
        typeof request.ssid !== 'string' || !request.ssid || Buffer.byteLength(request.ssid) > 32 ||
        typeof request.password !== 'string') {
      throw new InvalidRegistrationError();
    }
    let pairing;
    try {
      pairing = ManualPairingCodeCodec.decode(request.code);
    } catch {
      throw new InvalidRegistrationError();
    }
    commissioning = true;
    try {
      console.log(JSON.stringify({ progress: '등록 대기 기기 검색 중 (BLE 및 로컬 네트워크)' }));
      const peer = await controller.peers.commission({
        ...pairing,
        timeout: Seconds(60),
        discoveryCapabilities: { ble: true, onIpNetwork: true },
        wifiNetwork: { wifiSsid: request.ssid, wifiCredentials: request.password },
        regulatoryLocation: GeneralCommissioning.RegulatoryLocationType.IndoorOutdoor,
        regulatoryCountryCode: 'KR',
        onAttestationFailure: findings => findings.every(f => f.level !== 'error'),
      });
      return { id: peer.id };
    } finally {
      commissioning = false;
    }
  }
  if (!['status', 'on', 'off'].includes(request.op)) throw new Error('지원하지 않는 요청입니다.');
  const peer = [...controller.peers.commissioned].find(p => p.id === request.id);
  if (!peer || !peer.lifecycle.isConnected || !peer.lifecycle.isSeeded) throw new DeviceNotReadyError();
  const candidates = [...peer.endpoints].filter(endpoint => endpoint.behaviors.has(OnOffClient));
  if (candidates.length !== 1) throw new OnOffEndpointError();
  const endpoint = candidates[0];
  if (request.op === 'on') await endpoint.commandsOf(OnOffClient).on();
  if (request.op === 'off') await endpoint.commandsOf(OnOffClient).off();
  const { onOff } = await endpoint.getStateOf(OnOffClient, ['onOff'], { includeKnownVersions: true });
  return { endpoint: endpoint.number, onOff: typeof onOff === 'boolean' ? onOff : null };
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
      console.log(JSON.stringify({ ok: false, error: safeMatterError(error) }));
    }
  }
} catch (error) {
  console.log(JSON.stringify({ ready: false, error: safeMatterError(error) }));
  process.exitCode = 1;
} finally {
  if (controller) await controller.close();
}
