
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import uuid, html, json, base64

st.set_page_config(
    page_title="나의 작품을 소개합니다!",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = BASE_DIR / "gallery.db"
UPLOAD_DIR.mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            summary TEXT,
            content TEXT,
            thumbnail_path TEXT,
            detail_images TEXT,
            blog_url TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_post(author, title, category, summary, content, thumbnail_path, detail_images, blog_url):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO posts (
            author, title, category, summary, content,
            thumbnail_path, detail_images, blog_url, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        author, title, category, summary, content,
        thumbnail_path,
        json.dumps(detail_images, ensure_ascii=False),
        blog_url,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()

def get_posts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, author, title, category, summary, content,
               thumbnail_path, detail_images, blog_url, created_at
        FROM posts
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_posts_by_author(author):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, author, title, category, summary, content,
               thumbnail_path, detail_images, blog_url, created_at
        FROM posts
        WHERE author = ?
        ORDER BY id DESC
    """, (author,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_post(post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, author, title, category, summary, content,
               thumbnail_path, detail_images, blog_url, created_at
        FROM posts
        WHERE id = ?
    """, (post_id,))
    row = cur.fetchone()
    conn.close()
    return row

def delete_post(post_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

init_db()

if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_post" not in st.session_state:
    st.session_state.selected_post = None
if "selected_author" not in st.session_state:
    st.session_state.selected_author = None

def save_uploaded_file(file):
    if file is None:
        return None
    ext = file.name.split(".")[-1].lower()
    path = UPLOAD_DIR / f"{uuid.uuid4()}.{ext}"
    with open(path, "wb") as f:
        f.write(file.getbuffer())
    return str(path)

def image_to_base64(path):
    try:
        with open(path, "rb") as f:
            enc = base64.b64encode(f.read()).decode()
        suffix = Path(path).suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/webp" if suffix == ".webp" else "image/jpeg"
        return f"data:{mime};base64,{enc}"
    except:
        return ""

def safe_text(v):
    return "" if v is None else html.escape(str(v))

def initials(name):
    return "?" if not name else name[0]

def get_categories(posts):
    out = []
    for p in posts:
        c = (p[3] or "").strip()
        if c and c not in out:
            out.append(c)
    return out

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root{
--bg:#151412;--bg2:#1B1916;--panel:#211F1C;--text:#F7F1E8;--muted:#B8ADA0;
--accent:#D7A968;--line:#3E3730;--cream:#EDE1D1;
}
html,body,[class*="css"]{font-family:"Noto Sans KR",sans-serif;}
.stApp{
background:
radial-gradient(circle at 5% 0%,rgba(215,169,104,.14),transparent 430px),
radial-gradient(circle at 92% 25%,rgba(169,121,71,.07),transparent 420px),
linear-gradient(180deg,var(--bg),var(--bg2));
color:var(--text);
}
.block-container{max-width:1240px;padding-top:1.4rem;padding-bottom:5rem;}
#MainMenu,footer{visibility:hidden;} header{background:transparent!important;}
.brand{font-size:1.15rem;font-weight:800;color:var(--text);letter-spacing:-.03em;padding-top:.45rem;}
.brand span,.eyebrow,.section-label,.work-category,.work-view,.detail-meta{color:var(--accent);}
.hero{padding:4.5rem 0 3.2rem;}
.eyebrow,.section-label{font-size:.84rem;font-weight:700;letter-spacing:.16em;margin-bottom:1rem;}
.hero-title{color:var(--text);font-size:clamp(3rem,7vw,6.5rem);line-height:1.02;font-weight:800;letter-spacing:-.055em;margin:0;}
.hero-title span{color:var(--accent);}
.hero-desc{color:var(--muted);font-size:clamp(1rem,2vw,1.18rem);line-height:1.9;max-width:720px;margin-top:1.6rem;}
.profile-panel{display:flex;align-items:center;justify-content:space-between;gap:2rem;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:2rem 0;margin-bottom:2rem;}
.profile-left{display:flex;align-items:center;gap:1.3rem;}
.profile-avatar{width:74px;height:74px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#D7A968,#8F633B);color:#1A1713;font-size:1.8rem;font-weight:800;}
.profile-name{color:var(--text);font-size:1.7rem;font-weight:800;letter-spacing:-.04em;}
.profile-description{color:var(--muted);font-size:.92rem;margin-top:.3rem;}
.profile-stats{display:flex;gap:2rem}.stat{text-align:center}.stat-number{color:var(--text);font-size:1.5rem;font-weight:800}.stat-label{color:var(--muted);font-size:.78rem}
.section-label{margin-top:2.5rem;margin-bottom:.5rem;}
.section-title{color:var(--text);font-size:clamp(1.9rem,4vw,2.8rem);font-weight:800;letter-spacing:-.04em;margin-bottom:1.7rem;}
.featured-card,.work-card{position:relative;border-radius:28px;overflow:hidden;background:var(--panel);border:1px solid rgba(255,255,255,.06);}
.featured-card{min-height:520px;margin-bottom:2rem}.featured-card img{width:100%;height:520px;object-fit:cover;display:block}
.featured-overlay,.work-overlay{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:flex-end;background:linear-gradient(180deg,transparent 30%,rgba(0,0,0,.86));}
.featured-overlay{padding:2.2rem}.work-overlay{padding:1.4rem}
.featured-label{color:var(--accent);font-size:.8rem;font-weight:700;letter-spacing:.12em}
.featured-title{color:white;font-size:clamp(2rem,5vw,4rem);font-weight:800;line-height:1.1;margin:.55rem 0}
.featured-meta,.work-meta{color:rgba(255,255,255,.68);font-size:.9rem}
.work-card{min-height:390px;box-shadow:0 16px 32px rgba(0,0,0,.14)}
.work-card img{width:100%;height:390px;object-fit:cover;display:block;transition:transform .35s ease}
.work-card:hover img{transform:scale(1.04)}
.work-category{font-size:.76rem;font-weight:700;letter-spacing:.11em;margin-bottom:.45rem}
.work-title{color:white;font-size:1.35rem;font-weight:800;line-height:1.3}
.work-view{font-size:.78rem;font-weight:700;letter-spacing:.1em;margin-top:.85rem}
.detail-title{color:var(--text);font-size:clamp(2.8rem,6vw,5.8rem);font-weight:800;line-height:1.05;letter-spacing:-.05em;margin:.6rem 0 1rem}
.detail-summary{color:var(--muted);max-width:760px;line-height:1.8;font-size:1.18rem}
.story-box{max-width:820px;font-size:1.05rem;line-height:2.1;color:var(--cream);padding:1rem 0 3rem}
.stButton>button{width:100%;border-radius:13px;border:1px solid #4A4239;background:#29251F;color:var(--cream);font-weight:600}
.stButton>button:hover{border-color:var(--accent);color:var(--accent);background:#332C25}
.stTextInput input,.stTextArea textarea{background:#211F1C;color:var(--cream);border:1px solid #413A33;border-radius:13px}
@media(max-width:768px){
.block-container{padding-left:1rem;padding-right:1rem}
.hero{padding:2.4rem 0 2rem}
.profile-panel{flex-direction:column;align-items:flex-start}
.profile-stats{width:100%;justify-content:space-between}
.featured-card{min-height:360px}.featured-card img{height:360px}
.work-card{min-height:320px}.work-card img{height:320px}
}
</style>
""", unsafe_allow_html=True)

def go_home():
    st.session_state.page = "home"
    st.session_state.selected_post = None
    st.session_state.selected_author = None
    st.rerun()

def top_nav():
    c1,c2,c3,c4 = st.columns([5,1.3,1.3,1.3])
    with c1:
        st.markdown('<div class="brand">OUR CLASS <span>GALLERY</span></div>', unsafe_allow_html=True)
    with c2:
        if st.button("전체 작품", use_container_width=True):
            go_home()
    with c3:
        if st.button("내 작품", use_container_width=True):
            st.session_state.selected_author = st.session_state.user_name
            st.session_state.page = "portfolio"
            st.rerun()
    with c4:
        if st.button("+ 작품 등록", use_container_width=True):
            st.session_state.page = "upload"
            st.rerun()

def login_page():
    left,right = st.columns([1.2,.8],gap="large")
    with left:
        st.markdown("""
        <div class="hero">
        <div class="eyebrow">OUR CLASS · ONLINE EXHIBITION</div>
        <h1 class="hero-title">나의 작품을<br><span>소개합니다!</span></h1>
        <div class="hero-desc">우리가 직접 만든 작품과 그 안에 담긴 이야기를 기록하는 우리 반 온라인 전시관입니다.<br><br>이름을 입력하고 나만의 작품 공간을 시작해보세요.</div>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-label">ENTER GALLERY</div><div class="section-title">이름으로 입장하기</div>', unsafe_allow_html=True)
        name = st.text_input("이름", placeholder="예: 김하늘", label_visibility="collapsed")
        if st.button("나의 작품 공간 시작하기 →", use_container_width=True):
            if name.strip():
                st.session_state.user_name = name.strip()
                st.session_state.page = "home"
                st.rerun()
            else:
                st.warning("이름을 입력해주세요.")

def render_profile_summary():
    my_posts = get_posts_by_author(st.session_state.user_name)
    all_posts = get_posts()
    st.markdown(f"""
    <div class="profile-panel">
      <div class="profile-left">
        <div class="profile-avatar">{safe_text(initials(st.session_state.user_name))}</div>
        <div>
          <div class="profile-name">{safe_text(st.session_state.user_name)}의 작품 공간</div>
          <div class="profile-description">나만의 작품과 이야기를 기록해보세요.</div>
        </div>
      </div>
      <div class="profile-stats">
        <div class="stat"><div class="stat-number">{len(my_posts)}</div><div class="stat-label">MY WORKS</div></div>
        <div class="stat"><div class="stat-number">{len(all_posts)}</div><div class="stat-label">CLASS WORKS</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_work_card(post,index):
    post_id,author,title,category,summary,content,thumbnail_path,detail_images,blog_url,created_at = post
    src = image_to_base64(thumbnail_path) if thumbnail_path and Path(thumbnail_path).exists() else ""
    image_html = f'<img src="{src}">' if src else '<div style="height:390px;background:linear-gradient(135deg,#3a3028,#1f1c19)"></div>'
    st.markdown(f"""
    <div class="work-card">
      {image_html}
      <div class="work-overlay">
        <div class="work-category">{safe_text(category or "ART WORK")}</div>
        <div class="work-title">{safe_text(title)}</div>
        <div class="work-meta">{safe_text(author)}</div>
        <div class="work-view">VIEW WORK →</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("작품 자세히 보기", key=f"open_{post_id}", use_container_width=True):
        st.session_state.selected_post = post_id
        st.session_state.page = "detail"
        st.rerun()

def home_page():
    top_nav()
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">OUR CLASS · ONLINE EXHIBITION</div>
      <h1 class="hero-title">나의 작품을<br><span>소개합니다!</span></h1>
      <div class="hero-desc">작은 아이디어에서 시작해 직접 만들고 완성한 작품들.<br>우리 반 친구들의 다양한 작품과 이야기를 만나보세요.</div>
    </div>
    """, unsafe_allow_html=True)
    render_profile_summary()
    posts = get_posts()

    if posts:
        latest = posts[0]
        post_id,author,title,category,summary,content,thumbnail_path,detail_images,blog_url,created_at = latest
        if thumbnail_path and Path(thumbnail_path).exists():
            src = image_to_base64(thumbnail_path)
            st.markdown('<div class="section-label">FEATURED WORK</div><div class="section-title">최근 작품</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="featured-card">
              <img src="{src}">
              <div class="featured-overlay">
                <div class="featured-label">NEW WORK</div>
                <div class="featured-title">{safe_text(title)}</div>
                <div class="featured-meta">{safe_text(author)} · {safe_text(category or "ART WORK")}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("최근 작품 보러가기 →", key="latest_post", use_container_width=True):
                st.session_state.selected_post = post_id
                st.session_state.page = "detail"
                st.rerun()

    st.markdown('<div class="section-label">CATEGORY</div><div class="section-title">작품 둘러보기</div>', unsafe_allow_html=True)
    categories = ["전체"] + get_categories(posts)
    selected = st.radio("카테고리", categories, horizontal=True, label_visibility="collapsed")
    filtered_posts = [p for p in posts if p[3] == selected] if selected != "전체" else posts

    if not filtered_posts:
        st.info("아직 등록된 작품이 없습니다. 첫 작품을 올려보세요!")
        return

    cols = st.columns(3, gap="large")
    for index,post in enumerate(filtered_posts):
        with cols[index % 3]:
            render_work_card(post,index)

def portfolio_page():
    top_nav()
    author = st.session_state.selected_author or st.session_state.user_name
    posts = get_posts_by_author(author)
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">STUDENT PORTFOLIO</div>
      <h1 class="hero-title">{safe_text(author)}의<br><span>작품 공간</span></h1>
      <div class="hero-desc">직접 만들고 기록한 개인 작품 포트폴리오입니다.</div>
    </div>
    """, unsafe_allow_html=True)

    if not posts:
        st.info("아직 등록된 작품이 없습니다.")
        return

    cols = st.columns(3, gap="large")
    for index,post in enumerate(posts):
        with cols[index % 3]:
            render_work_card(post,index)

def upload_page():
    top_nav()
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">NEW WORK</div>
      <h1 class="hero-title">새로운 작품을<br><span>기록해보세요.</span></h1>
      <div class="hero-desc">작품 사진과 제작 과정을 함께 남겨 나만의 포트폴리오를 만들어보세요.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("new_post_form"):
        title = st.text_input("작품 이름", placeholder="예: 올리브 미니백")
        category = st.text_input("작품 종류", placeholder="예: 가죽공예")
        summary = st.text_input("한 줄 소개", placeholder="예: 처음으로 완성한 나의 작은 가죽가방")
        thumbnail = st.file_uploader("대표 이미지", type=["jpg","jpeg","png","webp"])
        detail_files = st.file_uploader("상세 이미지", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
        content = st.text_area("작품 이야기", placeholder="작품을 만들게 된 이유, 어려웠던 점, 마음에 드는 부분, 완성하고 느낀 점 등을 자유롭게 적어보세요.", height=300)
        blog_url = st.text_input("블로그 주소", placeholder="https://blog.naver.com/...")
        submitted = st.form_submit_button("작품 등록하기 →", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("작품 이름을 입력해주세요.")
            return

        thumbnail_path = save_uploaded_file(thumbnail)
        detail_paths = [save_uploaded_file(f) for f in detail_files] if detail_files else []

        insert_post(
            st.session_state.user_name,
            title.strip(),
            category.strip(),
            summary.strip(),
            content.strip(),
            thumbnail_path,
            detail_paths,
            blog_url.strip()
        )
        st.success("작품이 등록되었습니다! 🎉")
        st.session_state.page = "home"
        st.rerun()

def detail_page():
    post_id = st.session_state.selected_post
    if not post_id:
        go_home()

    post = get_post(post_id)
    if post is None:
        st.error("게시글을 찾을 수 없습니다.")
        return

    post_id,author,title,category,summary,content,thumbnail_path,detail_images_json,blog_url,created_at = post

    try:
        detail_images = json.loads(detail_images_json) if detail_images_json else []
    except:
        detail_images = []

    if st.button("← BACK TO GALLERY"):
        go_home()

    st.markdown(f"""
    <div class="section-label">{safe_text(category or "ART WORK")}</div>
    <div class="detail-title">{safe_text(title)}</div>
    <div class="detail-summary">{safe_text(summary)}</div>
    <div class="detail-meta">{safe_text(author)} · {safe_text(created_at)}</div>
    """, unsafe_allow_html=True)

    if thumbnail_path and Path(thumbnail_path).exists():
        st.image(thumbnail_path, use_container_width=True)

    st.markdown('<div class="section-label">ABOUT THIS WORK</div><div class="section-title">작품 이야기</div>', unsafe_allow_html=True)
    content_html = safe_text(content).replace("\n","<br>")
    st.markdown(f'<div class="story-box">{content_html}</div>', unsafe_allow_html=True)

    if detail_images:
        st.markdown('<div class="section-label">DETAIL CUT</div><div class="section-title">작품을 더 자세히</div>', unsafe_allow_html=True)
        for image_path in detail_images:
            if Path(image_path).exists():
                st.image(image_path, use_container_width=True)

    if blog_url:
        st.link_button("NAVER BLOG에서 전체 이야기 보기 ↗", blog_url, use_container_width=True)

    if st.button(f"{author}의 다른 작품 보기 →", use_container_width=True):
        st.session_state.selected_author = author
        st.session_state.page = "portfolio"
        st.rerun()

    if author == st.session_state.user_name:
        with st.expander("게시글 관리"):
            st.caption("내가 작성한 작품입니다.")
            if st.button("이 작품 삭제하기"):
                delete_post(post_id)
                go_home()

if st.session_state.user_name is None:
    login_page()
else:
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "portfolio":
        portfolio_page()
    elif st.session_state.page == "upload":
        upload_page()
    elif st.session_state.page == "detail":
        detail_page()
