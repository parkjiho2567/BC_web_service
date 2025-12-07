from flask import Flask, render_template, request, send_file
import bcsfe
import io
import traceback # 오류 추적용

app = Flask(__name__)

# BCSFE에서 사용하는 아이템 ID
ITEM_IDS = {
    'RARE_TICKET': 11,
    'PLAT_TICKET': 12,
    'LEADERSHIP': 13
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 1. 파일 업로드 확인 및 데이터 읽기
            uploaded_file = request.files.get('save_file')
            if not uploaded_file or uploaded_file.filename == '':
                raise Exception("세이브 파일(.sav)을 선택해주세요.")
            
            file_data = uploaded_file.read()
            
            # 2. bcsfe로 세이브 파일 로드
            save_data = bcsfe.core.SaveFile(file_data)

            # 3. 데이터 수정 (최신 라이브러리 구조에 맞게 try-except 포함)
            
            # 재화 수정
            cf = int(request.form.get('catfood', 45000))
            xp = int(request.form.get('xp', 99999999))
            np = int(request.form.get('np', 50000))

            # cat_food, xp, np 속성에 직접 접근하거나 setter 사용
            if hasattr(save_data, 'cat_food') and hasattr(save_data.cat_food, 'value'):
                save_data.cat_food.value = cf
                save_data.xp.value = xp
                save_data.np.value = np
            else:
                # 구버전 또는 다른 구조일 경우 대비 (안전한 set_ 함수 사용)
                save_data.set_cat_food(cf)
                save_data.set_xp(xp)
                save_data.set_np(np) 
            
            # 아이템 수정
            rt = int(request.form.get('rare_ticket', 0))
            pt = int(request.form.get('plat_ticket', 0))
            
            if hasattr(save_data, 'set_item_amount'):
                save_data.set_item_amount(ITEM_IDS['RARE_TICKET'], rt)
                save_data.set_item_amount(ITEM_IDS['PLAT_TICKET'], pt)
                
                # 무제한 아이템 설정
                if request.form.get('infinite_items'):
                    save_data.set_item_amount(ITEM_IDS['LEADERSHIP'], 999) # 리더십
                    save_data.set_item_amount(15, 999) # 트레저 레이더
                    save_data.set_item_amount(28, 999) # 스피드업
            
            # 4. 수정된 파일 저장 및 다운로드 준비
            output_buffer = io.BytesIO()
            new_data = save_data.to_data()
            output_buffer.write(new_data.to_bytes())
            output_buffer.seek(0)
            
            # 5. 파일을 다운로드로 응답
            return send_file(
                output_buffer,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name='save_modified.sav'
            )

        except Exception as e:
            traceback.print_exc()
            return render_template('index.html', error=f"세이브 파일 처리 중 오류가 발생했습니다: {str(e)}")

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
