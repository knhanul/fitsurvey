import os
from app import get_equipment_list

def check_image_display():
    """이미지 표시 문제 확인"""
    equipment_list = get_equipment_list()
    
    print('이미지 표시 확인:')
    print('=' * 60)
    
    # 첫 번째 장비 확인
    first_equipment = equipment_list[0]
    equipment_id = first_equipment['id']
    item_name = first_equipment['item_name']
    
    print(f'첫 번째 장비 (인덱스 0):')
    print(f'  ID: {equipment_id}')
    print(f'  이름: {item_name}')
    print(f'  기대 이미지: eq_{equipment_id}_photo.png')
    
    # 실제 이미지 파일 확인
    photo_path = f'assets/images/eq_{equipment_id}_photo.png'
    if os.path.exists(photo_path):
        print(f'  ✅ 이미지 파일 존재: {photo_path}')
    else:
        print(f'  ❌ 이미지 파일 없음: {photo_path}')
    
    # eq_3_photo.png 확인
    eq_3_path = 'assets/images/eq_3_photo.png'
    if os.path.exists(eq_3_path):
        print(f'  ✅ eq_3_photo.png 존재')
        eq_3_equipment = next((eq for eq in equipment_list if eq['id'] == 3), None)
        if eq_3_equipment:
            print(f'     eq_3 장비: {eq_3_equipment["item_name"]} (인덱스 {equipment_list.index(eq_3_equipment)})')
    else:
        print(f'  ❌ eq_3_photo.png 없음')
    
    print()
    print('앱에서 표시되는 순서:')
    for i, equipment in enumerate(equipment_list[:5]):
        print(f'  {i}위: ID {equipment["id"]} - {equipment["item_name"]}')
    
    print()
    print('해결 방법:')
    print('1. 앱을 재시작하여 Session State 초기화')
    print('2. 브라우저 캐시 삭제')
    print('3. Streamlit 캐시 초기화: streamlit cache clear')

if __name__ == '__main__':
    check_image_display()
