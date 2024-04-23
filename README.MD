## TODO 홈페이지 구현

기본 예제코드 전부 삭제하고 직접 todos와 auth를 구현
Starting Files.zip을 풀면 기본 예제코드 및 웹 코드 있음


todos.db에 임시로 만든 ID/PW
* testuser / password
---

0. html을 확인하여 전달받는 변수명 확인
1. home.html이 메인페이지로 지정
2. 로그인이 안되어 있을시 login.html로 변경
3. JWT를 사용하여 로그인 기능 구현
4. add-todo,edit-todo,delete,complete 기능 구현
5. 로그인 만료시 자동으로 로그아웃 진행
6. 에러 발생시 content에 "msg" 값을 넣어 에러 출력
7. 회원가입 시 Unique, 기본키 유의해서 데이터 받기

---
## 실패
1. 로그아웃 버튼 만들기 -> nvbar.html에서 logout 버튼이 할당 되어있는걸로 확인있지만
실제로 생성이 안됨
   
2. JWT 만료이후로 쿠키삭제 -> 코드로는 구현이 되어있지만 실제로는 삭제가 안됨
일단 기능적으로 문제는 없음

