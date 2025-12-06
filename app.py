from flask import Flask, render_template, request
import bcsfe
# 🛑 중요: Server 모듈을 올바른 경로에서 불러옵니다.
try:
    from bcsfe.core.server.server import Server
except ImportError:
    # 만약 위 경로가 실패하면 다른 경로 시도 (구버전 호환)
    try:
        from bcsfe.server import Server
    except ImportError:
        # 최후의 수단: 메인 패키지에서 찾기
        Server = bcsfe.core.Server

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
            # 1. 폼 데이터 가져오기
            t_code = request.form.get('transfer_code')
            c_code = request.form.get('confirm_code')
            cc = request.form.get('country_code', 'KR').lower() # 소문자로 변환
            did = request.form.get('device_id')
            
            # 2. 서버에서 세이브 파일 다운로드
            # Server.download_save(인계코드, 인증코드, 국가, 기기ID, 버전)
            save_data = Server.download_save(t_code, c_code, cc, did, None)
            
            if not save_data:
                raise Exception("세이브 파일을 다운로드하지 못했습니다. 코드를 확인해주세요.")

            # 3. 데이터 수정 (치트 적용)
            # 재화
            save_data.cat_food = int(request.form.get('catfood', 0))
            save_data.xp = int(request.form.get('xp', 0))
            save_data.np = int(request.form.get('np', 0))
            
            # 티켓
            save_data.set_item_amount(ITEM_IDS['RARE_TICKET'], int(request.form.get('rare_ticket', 0)))
            save_data.set_item_amount(ITEM_IDS['PLAT_TICKET'], int(request.form.get('plat_ticket', 0)))

            # 편의 기능
            if request.form.get('infinite_energy'):
                save_data.set_item_amount(ITEM_IDS['LEADERSHIP'], 999)
            
            if request.form.get('infinite_items'):
                # 트레저 레이더 등 주요 아이템 999개 지급
                for item_id in [15, 16, 17, 18, 19]: 
                    save_data.set_item_amount(item_id, 999)

            if request.form.get('unlock_all_cats'):
                # 고양이 전체 해금 (사용 주의)
                cats = save_data.cats.cats
                for cat in cats:
                    cat.unlock()

            # 4. 서버로 업로드 및 새 코드 발급
            upload_result = Server.upload_save(save_data, cc, did)
            
            if not upload_result:
                 raise Exception("업로드에 실패했습니다. 잠시 후 다시 시도해주세요.")
            
            new_t_code = upload_result['transfer_code']
            new_c_code = upload_result['confirmation_code']

            # 5. 결과 메시지 생성
            success_msg = (
                f"Transfer Code: {new_t_code}\n"
                f"Confirmation Code: {new_c_code}\n\n"
                "⚠️ 게임 타이틀 화면에서 '이어하기'를 눌러 위 코드를 입력하세요."
            )
            
            return render_template('index.html', success_message=success_msg)

        except Exception as e:
            # 오류 발생 시 화면에 표시
            return render_template('index.html', error=str(e))

    # GET 요청 시 페이지만 보여줌
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
