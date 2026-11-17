// 오류 종류만 허용 목록으로 노출합니다. 코드와 네트워크 정보는 기록하지 않습니다.
const messages = {
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
  for (let current = error; current && typeof current === 'object' && !seen.has(current); current = current.cause) {
    seen.add(current);
    const name = current.constructor?.name;
    if (Object.hasOwn(messages, name)) names.push(name);
  }
  if (names.length) return `${messages[names[0]]} (${names.join(' → ')})`;
  return 'Matter 요청에 실패했습니다. 기기의 등록 모드와 Bluetooth·네트워크를 확인하세요.';
}
