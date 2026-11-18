// 오류 종류만 허용 목록으로 노출합니다. 코드와 네트워크 정보는 기록하지 않습니다.
const messages = {
  InvalidRegistrationError: 'Matter 숫자 코드와 Wi-Fi 이름을 확인하세요.',
  DeviceNotDiscoveredError: '설정 코드와 일치하는 등록 대기 기기를 찾지 못했습니다.',
  NoDiscoveryTransportError: '사용 가능한 Matter 기기 검색 경로가 없습니다.',
  WifiNetworkSetupFailedError: '플러그가 Wi-Fi에 연결하지 못했습니다. 2.4GHz 네트워크 이름과 비밀번호를 확인하세요.',
  OperativeConnectionFailedError: '등록 중 플러그에 IP로 다시 연결하지 못했습니다. 로컬 IPv6와 mDNS 통신을 확인하세요.',
  CommissioningTimeoutError: 'Matter 등록 세션의 시간이 초과되었습니다.',
  DeviceAttestationError: '플러그의 Matter 기기 인증을 완료하지 못했습니다.',
  DeviceNotReadyError: '등록한 기기가 아직 준비되지 않았습니다. 네트워크에 연결된 뒤 다시 시도하세요.',
  OnOffEndpointError: '단일 On/Off 제어 지점을 찾지 못했습니다.',
  TimeoutError: '기기 검색 또는 등록 중 시간이 초과되었습니다.',
  PasscodeMismatchError: 'Matter 설정 코드가 기기와 일치하지 않습니다.',
  BleError: 'Bluetooth 연결에 실패했습니다.',
  BleDisconnectedError: 'Bluetooth 연결이 끊겼습니다.',
  NetworkUnreachableError: '기기에 연결할 네트워크 경로를 찾지 못했습니다.',
  AddressUnreachableError: '기기 주소에 연결할 수 없습니다.',
  StorageLockError: '다른 Matter 컨트롤러가 저장소를 사용 중입니다.',
  CertificateError: '기기 인증서를 검증하지 못했습니다.',
};

export function safeMatterError(error) {
  const names = [];
  const seen = new Set();
  const pending = [error];
  while (pending.length) {
    const current = pending.pop();
    if (!current || typeof current !== 'object' || seen.has(current)) continue;
    seen.add(current);
    const name = current.constructor?.name;
    if (Object.hasOwn(messages, name) && !names.includes(name)) names.push(name);
    if (current instanceof AggregateError) pending.push(...current.errors);
    pending.push(current.cause);
  }
  if (names.length) return `${messages[names[0]]} (${names.join(' → ')})`;
  return 'Matter 요청에 실패했습니다. 기기의 등록 모드와 Bluetooth·네트워크를 확인하세요.';
}
