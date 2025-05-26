#!/usr/bin/env python
"""
테스트 실행 스크립트
Flask 블로그 애플리케이션의 모든 테스트를 실행합니다.
"""
import os
import sys
import importlib
import argparse

# 프로젝트 루트 경로를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def discover_test_modules():
    """tests 디렉토리에서 모든 테스트 모듈 탐색"""
    test_modules = []
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        if '__pycache__' in root:
            continue
            
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                # 절대 경로에서 상대 모듈 경로로 변환
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                module_path = rel_path.replace(os.path.sep, '.').replace('.py', '')
                test_modules.append(module_path)
    
    return test_modules

def run_all_tests():
    """모든 테스트 모듈 실행"""
    test_modules = discover_test_modules()
    print(f"발견된 테스트 모듈: {len(test_modules)}")
    
    for module_path in test_modules:
        print(f"\n{'='*50}")
        print(f"실행 중: {module_path}")
        print(f"{'='*50}")
        
        try:
            module = importlib.import_module(module_path)
            
            # 모듈에 run_all_tests 함수가 있으면 실행
            if hasattr(module, 'run_all_tests'):
                module.run_all_tests()
            # 또는 테스트 실행을 위한 run_test 함수가 있으면 실행
            elif hasattr(module, 'run_test'):
                module.run_test('check')
            else:
                print(f"WARNING: 모듈 {module_path}에 실행 가능한 테스트 함수가 없습니다.")
        
        except Exception as e:
            print(f"ERROR: 모듈 {module_path} 실행 중 오류 발생: {str(e)}")
    
    print("\n모든 테스트 완료!")

def run_specific_test(test_type):
    """특정 유형의 테스트만 실행"""
    test_modules = discover_test_modules()
    matching_modules = [m for m in test_modules if test_type in m]
    
    if not matching_modules:
        print(f"ERROR: '{test_type}' 유형의 테스트 모듈을 찾을 수 없습니다.")
        return
    
    print(f"발견된 '{test_type}' 테스트 모듈: {len(matching_modules)}")
    
    for module_path in matching_modules:
        print(f"\n{'='*50}")
        print(f"실행 중: {module_path}")
        print(f"{'='*50}")
        
        try:
            module = importlib.import_module(module_path)
            
            if hasattr(module, 'run_all_tests'):
                module.run_all_tests()
            elif hasattr(module, 'run_test'):
                module.run_test('check')
            else:
                print(f"WARNING: 모듈 {module_path}에 실행 가능한 테스트 함수가 없습니다.")
        
        except Exception as e:
            print(f"ERROR: 모듈 {module_path} 실행 중 오류 발생: {str(e)}")
    
    print(f"\n{test_type} 테스트 완료!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Flask 블로그 애플리케이션 테스트 실행')
    parser.add_argument('--type', choices=['db', 'category', 'utils', 'all'], 
                        default='all', help='실행할 테스트 유형 (db, category, utils, all)')
    
    args = parser.parse_args()
    
    if args.type == 'all':
        run_all_tests()
    elif args.type == 'db':
        run_specific_test('db_tests')
    elif args.type == 'category':
        run_specific_test('category_tests')
    elif args.type == 'utils':
        run_specific_test('utils')
