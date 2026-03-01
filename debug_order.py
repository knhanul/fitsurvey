import os
from app import get_equipment_list

def debug_equipment_order():
    """장비 순서와 이미지 매핑 디버깅"""
    equipment_list = get_equipment_list()
    
    print('DB에서 가져온 장비 순서:')
    print('=' * 80)
    
    for i, equipment in enumerate(equipment_list):
        equipment_id = equipment['id']
        item_name = equipment['item_name']
        category = equipment['category']
        
        photo_path = f'assets/images/eq_{equipment_id}_photo.png'
        spec_path = f'assets/images/eq_{equipment_id}_spec.png'
        
        photo_exists = os.path.exists(photo_path)
        spec_exists = os.path.exists(spec_path)
        
        print(f'{i+1:2d}위. ID {equipment_id:2d}: {category} - {item_name}')
        print(f'     사진: {"✅" if photo_exists else "❌"} {photo_path}')
        print(f'     스펙: {"✅" if spec_exists else "❌"} {spec_path}')
        print()
    
    print('=' * 80)
    print('문제 분석:')
    
    # 첫 번째 장비 확인
    first_equipment = equipment_list[0]
    print(f'첫 번째 장비: ID {first_equipment["id"]} - {first_equipment["item_name"]}')
    print(f'기대 이미지: eq_{first_equipment["id"]}_photo.png')
    
    # 이미지 파일 실제 존재 확인
    expected_photo = f'assets/images/eq_{first_equipment["id"]}_photo.png'
    if os.path.exists(expected_photo):
        print(f'✅ 기대 이미지 파일 존재: {expected_photo}')
    else:
        print(f'❌ 기대 이미지 파일 없음: {expected_photo}')
    
    # eq_3_photo.png 확인
    eq_3_photo = 'assets/images/eq_3_photo.png'
    if os.path.exists(eq_3_photo):
        print(f'✅ eq_3_photo.png 파일 존재')
        # eq_3에 해당하는 장비 찾기
        eq_3_equipment = next((eq for eq in equipment_list if eq['id'] == 3), None)
        if eq_3_equipment:
            print(f'   eq_3에 해당하는 장비: {eq_3_equipment["item_name"]}')
        else:
            print('   eq_3에 해당하는 장비 없음')
    else:
        print('❌ eq_3_photo.png 파일 없음')

if __name__ == '__main__':
    debug_equipment_order()
