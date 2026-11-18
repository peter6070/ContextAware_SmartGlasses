"""Matter 기기 등록과 목록 확인을 위한 로컬 명령."""
import argparse
import getpass
from software.matter_controller import MatterController


def main():
    parser = argparse.ArgumentParser(description='노트북에 Matter 플러그를 등록합니다.')
    parser.add_argument('command', choices=['register', 'list', 'status', 'on', 'off'])
    parser.add_argument('--device', help='등록된 장치 ID')
    args = parser.parse_args()
    controller = MatterController()
    try:
        if args.command == 'register':
            code = getpass.getpass('Matter 숫자 코드: ').strip().replace('-', '')
            ssid = input('플러그가 연결될 Wi-Fi 이름: ').strip()
            password = getpass.getpass('Wi-Fi 비밀번호: ')
            result = controller.commission(code, ssid, password, on_progress=lambda stage: print(stage, flush=True))
            print('등록 완료. 장치 ID:', result['id'])
        elif args.command == 'list':
            for device in controller.request('list')['devices']:
                print(device['id'], '연결됨' if device['connected'] else '오프라인')
        else:
            if not args.device:
                parser.error('--device가 필요합니다')
            print(controller.request(args.command, id=args.device))
    finally:
        controller.close()


if __name__ == '__main__':
    main()
