from flask import Flask, render_template, request, send_file, url_for
import bcsfe
import io
import os

app = Flask(__name__)

# BCSFE-Python 아이템 ID (버전에 따라 다를 수 있습니다. 정확한 ID 확인 필요)
ITEM_IDS = {
    'RARE_TICKET': 11,
    'PLAT_TICKET': 12,
    'TREASURE_RADAR': 15, # 예시 ID
    'LEADERSHIP_ITEM': 13 # 리더십 아이템 ID (LeaderShip을 직접 설정하는 것과는 다름)
}


def create_hacked_save(data):
    """
    BCSFE-Python을 사용하여 세이브 파일을 생성하고 모든 파라미터를 적용합니다.
    :param data: 폼에서 넘어온 모든 데이터 딕셔너리
    :return: 생성된 세이브 파일의 내용 (bytes)
    """
    try:
        # 1. 세이브 파일 객체 생성
        save_data = bcsfe.core.SaveFile.create_default() 

        # 2. 재화 및 XP 설정
        save_data.set_cat_food(data['catfood']) 
        save_data.set_xp(data['xp'])
        save_data.set_leadership(data['leader']) # 리더십 에너지 값

        # 3. 티켓 및 아이템 설정
        save_data.set_item_amount(ITEM_IDS['RARE_TICKET'], data['rare_ticket'])
        save_data.set_item_amount(ITEM_IDS['PLAT_TICKET'], data['plat_ticket'])

        # 4. 편의성 기능 (토글) 적용
        if data['infinite_energy']:
             # 무한 에너지를 위해 리더십을 최대치로 설정 (LeaderShip 값과 별개로 아이템 지급)
            save_data.set_item_amount(ITEM_IDS['LEADERSHIP_ITEM'], 999) 
            # *팁: save_data.set_unlimited_energy(True) 같은 BCSFE 기능이 있다면 활용

        if data['infinite_radar']:
            # 트레저 레이더 무제한 (수량을 매우 높게 설정)
            save_data.set_item_amount(ITEM_IDS['TREASURE_RADAR'], 999) 

        # 5. 세이브 파일 객체를 메모리 내의 바이트로 저장
        output_buffer = io.BytesIO()
        bcsfe.core.save_save_file(save_data, output_buffer)
        output_buffer.seek(0)
        
        return output_buffer

    except Exception as e:
        print(f"BCSFE Error: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 폼 데이터 수집 및 정수 변환
            form_data = {
                # 재화
                'catfood': int(request.form.get('catfood', 0)),
                'xp': int(request.form.get('xp', 0)),
                # 티켓 및 아이템
                'rare_ticket': int(request.form.get('rare_ticket', 0)),
                'plat_ticket': int(request.form.get('plat_ticket', 0)),
                'leader': int(request.form.get('leader', 0)),
                # 토글 버튼 (체크되지 않으면 None이 반환됨)
                'infinite_energy': request.form.get('infinite_energy') == '1',
                'infinite_radar': request.form.get('infinite_radar') == '1'
            }
            
            # BCSFE 로직 실행
            save_file_buffer = create_hacked_save(form_data)

            if save_file_buffer:
                # 파일 다운로드 응답
                return send_file(
                    save_file_buffer,
                    mimetype='application/octet-stream',
                    as_attachment=True,
                    download_name='bcsfe_modified.sav'
                )
            else:
                error_message = "세이브 파일 생성 중 심각한 오류가 발생했습니다. 서버 로그를 확인하세요."
                return render_template('index.html', error=error_message)

        except ValueError:
            error_message = "입력된 값 중 유효하지 않은 정수가 있습니다. 숫자를 확인해 주세요."
            return render_template('index.html', error=error_message)
        except Exception as e:
            error_message = f"알 수 없는 오류: {str(e)}"
            return render_template('index.html', error=error_message)
            
    # GET 요청 시 웹 페이지 렌더링
    return render_template('index.html', error=None)


if __name__ == '__main__':
    app.run(debug=True)
