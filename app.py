from flask import Flask, render_template, request, url_for
import bcsfe
import io
import os
import random
import time

app = Flask(__name__)

# BCSFE-Python 아이템 ID (일반적으로 사용되는 값)
# 주의: 이 ID는 BCSFE-Python 라이브러리 버전에 따라 다를 수 있습니다.
ITEM_IDS = {
    'RARE_TICKET': 11,
    'PLAT_TICKET': 12,
    'LEADERSHIP_ITEM': 13,
    'TREASURE_RADAR': 15,
    'CATAMIN_B': 30,
    'CATAMIN_C': 31,
    'CATAMIN_S': 32,
    'CATSEYE_COMMON': 54,
}


# --- BCSFE-Python 서버 통신 및 수정 함수 (최종 구현) ---
def process_save_via_codes(t_code, c_code, cc, did, data):
    """
    인계 코드로 데이터를 불러와 수정하고, 다시 서버로 보내 새로운 코드를 받는 함수입니다.
    """
    try:
        # 1. 인계 코드를 사용하여 냥코 서버에서 세이브 데이터 다운로드
        print(f"Downloading save for TCode: {t_code}, CCode: {c_code}, Country: {cc}")
        
        save_data = bcsfe.core.Server.download_save(
            t_code, 
            c_code, 
            cc, 
            did,
            game_version=None, # None으로 설정하면 라이브러리가 최신 버전을 시도함
        ) 
        
        # 2. 치트 값 적용 (사용자 입력 전체 반영)
        
        # 기본 재화
        save_data.set_cat_food(data['catfood']) 
        save_data.set_xp(data['xp'])
        save_data.set_leadership(data['leadership']) 
        save_data.set_np(data['np'])
        
        # 티켓/아이템
        save_data.set_item_amount(ITEM_IDS['RARE_TICKET'], data['rare_ticket'])
        save_data.set_item_amount(ITEM_IDS['PLAT_TICKET'], data['plat_ticket'])
        
        # 카타민/캣츠아이
        save_data.set_item_amount(ITEM_IDS['CATAMIN_B'], data['catamin_b'])
        save_data.set_item_amount(ITEM_IDS['CATAMIN_C'], data['catamin_c'])
        save_data.set_item_amount(ITEM_IDS['CATAMIN_S'], data['catamin_s'])
        save_data.set_item_amount(ITEM_IDS['CATSEYE_COMMON'], data['catseye_common'])
        
        # 편의성 토글
        if data['infinite_energy']:
            save_data.set_item_amount(ITEM_IDS['LEADERSHIP_ITEM'], 999) 

        if data['infinite_radar']:
            save_data.set_item_amount(ITEM_IDS['TREASURE_RADAR'], 999) 
            
        if data['max_user_rank']:
            # 유저 랭크를 안전한 최대값으로 설정하는 기능 (예시: 99999)
            save_data.set_user_rank(99999) 
        
        # 3. 수정된 세이브 데이터를 냥코 서버로 업로드 (Upload)
        print("Uploading modified save data to server...")
        new_t_code, new_c_code = bcsfe.core.Server.upload_save(
            save_data, 
            cc, 
            did
        ) 

        # 4. 결과 메시지 반환
        return (
            "🎉 계정 수정 및 서버 저장이 완료되었습니다!\n"
            f"Transfer Code: {new_t_code}\n"
            f"Confirmation Code: {new_c_code}"
        )

    except Exception as e:
        # 서버 통신 오류, 인증 오류 등을 잡아 사용자에게 전달
        print(f"Server Communication Error: {e}")
        # 오류 발생 시 오류 메시지를 포함하여 다시 던집니다.
        raise Exception(f"BCSFE 서버 통신 오류: {e}. 코드가 정확한지 확인하세요.") 

# --- 웹 라우팅 (결과 메시지 반환) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 1. 폼 데이터 수집
            t_code = request.form.get('transfer_code', '').strip()
            c_code = request.form.get('confirm_code', '').strip()
            cc = request.form.get('country_code', 'KR').upper()
            did = request.form.get('device_id', 'FFFFFFFFFFFFFFFF').strip()
            
            # 모든 폼 데이터를 수집 (int 변환)
            form_data = {
                'catfood': int(request.form.get('catfood', 0)),
                'xp': int(request.form.get('xp', 0)),
                'leadership': int(request.form.get('leadership', 0)), # Leadership Energy도 추가
                'np': int(request.form.get('np', 0)),
                'rare_ticket': int(request.form.get('rare_ticket', 0)),
                'plat_ticket': int(request.form.get('plat_ticket', 0)),
                'catamin_b': int(request.form.get('catamin_b', 0)),
                'catamin_c': int(request.form.get('catamin_c', 0)),
                'catamin_s': int(request.form.get('catamin_s', 0)),
                'catseye_common': int(request.form.get('catseye_common', 0)),
                
                # 토글 (체크되면 '1', 아니면 None -> bool로 변환)
                'infinite_energy': request.form.get('infinite_energy') == '1',
                'infinite_radar': request.form.get('infinite_radar') == '1',
                'max_user_rank': request.form.get('max_user_rank') == '1'
            }
            
            # 2. BCSFE 서버 통신 로직 실행
            result_message = process_save_via_codes(t_code, c_code, cc, did, form_data)

            # 3. 새로운 인계 코드를 웹 페이지에 출력
            return render_template('index.html', success_message=result_message)

        except Exception as e:
            error_message = f"계정 처리 중 오류: {str(e)}"
            return render_template('index.html', error=error_message)
            
    return render_template('index.html', error=None)

# if __name__ == '__main__': ...
