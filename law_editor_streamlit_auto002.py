
import streamlit as st
import requests
import xml.etree.ElementTree as ET

st.title("📘 부칙 개정 도우미 (자동화 버전)")

search_word = st.text_input("🔍 찾을 단어", placeholder="예: 지방법원")
replace_word = st.text_input("📝 바꿀 단어", placeholder="예: 지역법원")

OC = "chetera"

def get_law_list_from_api(query):
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100&search=2&knd=A0002&query={query}"
    res = requests.get(url)
    res.encoding = 'utf-8'
    if res.status_code == 200:
        try:
            root = ET.fromstring(res.content)
            return [law.findtext("법령상세링크") for law in root.findall("law")]
        except ET.ParseError:
            return []
    return []

def fetch_law_text_from_detail_link(link):
    if not link:
        return None
    url = "http://www.law.go.kr" + link.replace("type=HTML", "type=XML")
    res = requests.get(url)
    res.encoding = "utf-8"
    if res.status_code == 200:
        try:
            return ET.fromstring(res.content)
        except ET.ParseError:
            return None
    return None

def extract_amendment_sentences(xml_root, law_title, search_word, replace_word):
    amendments = []
    for article in xml_root.iter("조문"):
        number = article.findtext("조문번호")
        title = article.findtext("조문제목") or ""
        content = article.findtext("조문내용") or ""
        if search_word in title:
            sentence = f'제{number}조{title} 중 "{search_word}"을 "{replace_word}"으로 한다.'
            amendments.append(sentence)
        elif search_word in content:
            sentence = f'제{number}조 중 "{search_word}"을 "{replace_word}"으로 한다.'
            amendments.append(sentence)
    return amendments

def process_all_laws(search_word, replace_word):
    links = get_law_list_from_api(search_word)
    result = {}
    for idx, link in enumerate(links, start=1):
        xml_root = fetch_law_text_from_detail_link(link)
        if xml_root is None:
            continue
        law_title = xml_root.findtext("법령명_한글")
        if not law_title:
            continue
        sentences = extract_amendment_sentences(xml_root, law_title, search_word, replace_word)
        if sentences:
            numbered_title = f"{idx:02d}. {law_title} 일부를 다음과 같이 개정한다."
            result[numbered_title] = sentences
    return result

if st.button("🚀 시작하기") and search_word and replace_word:
    with st.spinner("법령을 검색하고 개정 문장을 생성 중입니다..."):
        result = process_all_laws(search_word, replace_word)
        if not result:
            st.warning("❌ 일치하는 결과가 없습니다.")
        else:
            lines = []
            for title, sentences in result.items():
                lines.append(title)
                for sentence in sentences:
                    lines.append(sentence)
                lines.append("")  # 줄바꿈

            final_text = "\n".join(lines)
            st.text_area("📄 결과 미리보기", final_text, height=400)

            st.download_button(
                label="📥 TXT 파일 다운로드",
                data=final_text.encode("utf-8"),
                file_name="amendments.txt",
                mime="text/plain"
            )
