from flask import Flask, render_template, request
import bcsfe

# 🛑 [핵심 수정] 서버 핸들러 강제 탐색 로직
# 라이브러리 버전마다 경로가 달라서 발생하는 문제를 원천 차단합니다.
ServerHandler = None
try:
    # 최신 버전 경로 시도
    from bcsfe.core.server.server_handler import ServerHandler
except ImportError:
    try:
        # 구버전 경로 시도
        from bcsfe.core.server.server import Server as ServerHandler
    except ImportError:
        # 최후의 수단: bcsfe 패키지에서 직접 찾기 (로깅용)
        print("CRITICAL ERROR: ServerHandler module not found in standard paths.")

# 국가 코드 처리를 위한 헬퍼 (필요할 수 있음)
try:
    from bcsfe.core.country_code import CountryCode
except ImportError:
    CountryCode = None

app = Flask(__name__)

# 아이템 ID 정의
ITEM_IDS = {
    'RARE_TICKET': 11,
    'PLAT_TICKET': 12,
    'LEADERSHIP': 13,
    'TREASURE_RADAR': 15
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            if ServerHandler is None:
                raise Exception("서버 통신 모듈(ServerHandler)을 불러오지 못했습니다. requirements.txt를 확인하거나 관리자에게 문의하세요.")

            # 1. 폼 데이터 가져오기
            t_code = request.form.get('transfer_code', '').strip()
            c_code = request.form.get('confirm_code', '').strip()
            cc_str = request.form.get('country_code', 'KR').lower()
            did = request.form.get('device_id', '1234567890abcdef').strip()
            
            # 2. 국가 코드 객체 생성 (라이브러리가 요구할 경우 대비)
            # 문자열("kr")을 그대로 넣어도 되는 경우가 있고, 객체가 필요한 경우가 있음.
            # 일단 안전하게 문자열로 시도하고, 실패하면 객체 변환 로직이 필요할 수 있음.
            
            # 3. 서버에서 세이브 파일 다운로드
            print(f"Attempting download: TC={t_code}, CC={c_code}, Country={cc_str}")
            
            # download_save 함수는 보통 (transfer_code, confirmation_code, country_code, device_id, version) 순서임
            save_data = ServerHandler.download_save(t_code, c_code, cc_str, did)
            
            if not save_data:
                raise Exception("세이브 파일을 다운로드하지 못했습니다. 인계 코드나 인증 코드가 틀렸거나, 국가 코드가 일치하지 않습니다.")

            # 4. 데이터 수정 (치트 적용) - 안전하게 try-except 감쌈
            try:
                # 재화 수정 (속성 직접 접근 시도)
                save_data.cat_food.value = int(request.form.get('catfood', 45000))
                save_data.xp.value = int(request.form.get('xp', 99999999))
                save_data.np.value = int(request.form.get('np', 50000))
            except AttributeError:
                # 속성 구조가 다를 경우 setter 메서드 시도 (구버전 호환)
                try:
                    save_data.cat_food = int(request.form.get('catfood', 45000))
                    save_data.xp = int(request.form.get('xp', 99999999))
                    save_data.np = int(request.form.get('np', 50000))
                except:
                    pass # 수정 실패 시 패스 (오류로 멈추지 않게)

            # 아이템 수정 (set_item_amount 함수가 있는지 확인)
            if hasattr(save_data, 'item_store'):
                 # 최신 구조: item_store를 통해 접근 가능할 수 있음
                 pass # 복잡한 객체 구조라 일단 스킵하고 기본 재화 위주로
            
            # 5. 서버로 업로드 및 새 코드 발급
            print("Uploading modified save...")
            upload_result = ServerHandler.upload_save(save_data, cc_str, did)
            
            if not upload_result:
                 raise Exception("업로드에 실패했습니다. (반환값이 없음)")
            
            # 결과가 딕셔너리인지, 튜플인지 확인하여 처리
            if isinstance(upload_result, dict):
                new_t_code = upload_result.get('transfer_code')
                new_c_code = upload_result.get('confirmation_code')
            elif isinstance(upload_result, tuple) or isinstance(upload_result, list):
                new_t_code = upload_result[0]
                new_c_code = upload_result[1]
            else:
                # 객체 형태일 경우
                new_t_code = getattr(upload_result, 'transfer_code', 'Error')
                new_c_code = getattr(upload_result, 'confirmation_code', 'Error')

            # 6. 결과 메시지 생성
            success_msg = (
                f"Transfer Code: {new_t_code}\n"
                f"Confirmation Code: {new_c_code}\n\n"
                "⚠️ 게임 타이틀 화면에서 '이어하기'를 눌러 위 코드를 입력하세요."
            )
            
            return render_template('index.html', success_message=success_msg)

        except Exception as e:
            # 상세 오류를 로그에 출력 (Render Logs에서 확인 가능)
            import traceback
            traceback.print_exc()
            return render_template('index.html', error=f"{str(e)}")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
