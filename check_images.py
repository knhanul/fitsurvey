import os
from app import get_equipment_list

def check_image_matching():
    """기구명과 이미지 파일 일치 여부 확인"""
    equipment_list = get_equipment_list()
    
    print(f'총 장비 수: {len(equipment_list)}')
    print('=' * 60)
    
    mismatched = []
    missing_images = []
    
    for equipment in equipment_list:
        equipment_id = equipment['id']
        item_name = equipment['item_name']
        
        photo_path = f'assets/images/eq_{equipment_id}_photo.png'
        spec_path = f'assets/images/eq_{equipment_id}_spec.png'
        
        photo_exists = os.path.exists(photo_path)
        spec_exists = os.path.exists(spec_path)
        
        if not photo_exists or not spec_exists:
            missing_images.append({
                'id': equipment_id,
                'name': item_name,
                'photo': photo_exists,
                'spec': spec_exists
            })
        
        print(f'ID {equipment_id:2d}: {item_name}')
        print(f'  사진: {"✅" if photo_exists else "❌"} {photo_path}')
        print(f'  스펙: {"✅" if spec_exists else "❌"} {spec_path}')
        print()
    
    print('=' * 60)
    print(f'결과 요약:')
    print(f'전체 장비: {len(equipment_list)}개')
    print(f'이미지 누락: {len(missing_images)}개')
    
    if missing_images:
        print('\n❌ 이미지가 없는 장비:')
        for item in missing_images:
            print(f'  ID {item["id"]}: {item["name"]}')
            if not item['photo']:
                print(f'    - 사진 누락: {item["photo"]}')
            if not item['spec']:
                print(f'    - 스펙 누락: {item["spec"]}')

if __name__ == '__main__':
    check_image_matching()
