const form = document.querySelector('#search-form');
const query = document.querySelector('#query');
const button = form?.querySelector('button');
const result = document.querySelector('#result');
const answer = document.querySelector('#answer');
const askedQuestion = document.querySelector('#asked-question');
const matches = document.querySelector('#matches');
const chatHistory = document.querySelector('#chat-history');
const chatClear = document.querySelector('#chat-clear');
const chatFilmSearch = document.querySelector('#chat-film-search');
const chatFilmResults = document.querySelector('#chat-film-results');
const chatFilmPicker = document.querySelector('#chat-film-picker');
const chatSelectedMovie = document.querySelector('#chat-selected-movie');
const chatSelectedTitle = document.querySelector('#chat-selected-title');
const chatSelectedMeta = document.querySelector('#chat-selected-meta');
const chatChangeMovie = document.querySelector('#chat-change-movie');
const chatSpoilerOff = document.querySelector('#chat-spoiler-off');
const chatSpoilerOn = document.querySelector('#chat-spoiler-on');
const quizButton = document.querySelector('#quiz-button');
const quizNav = document.querySelector('#quiz-nav');
const quizHome = document.querySelector('#quiz-home');
const quizCard = document.querySelector('.quiz-card');
const quiz = document.querySelector('#quiz');
const quizRewardBar = document.querySelector('.quiz-reward-bar');
const quizTopline = document.querySelector('.quiz-topline');
const quizQuestionRow = document.querySelector('#quiz-question-row');
const quizCategory = document.querySelector('#quiz-category');
const quizQuestion = document.querySelector('#quiz-question');
const quizChoices = document.querySelector('#quiz-choices');
const quizFeedback = document.querySelector('#quiz-feedback');
const nextQuestion = document.querySelector('#next-question');
const finishQuiz = document.querySelector('#finish-quiz');
const quizSummary = document.querySelector('#quiz-summary');
const quizPoster = document.querySelector('#quiz-poster');
const quizPosterImage = document.querySelector('#quiz-poster-image');
const quizXp = document.querySelector('#quiz-xp');
const quizBadgeCount = document.querySelector('#quiz-badge-count');
const moodForm = document.querySelector('#mood-form');
const moodInput = document.querySelector('#mood-input');
const moodHero = document.querySelector('#focus');
const recommendations = document.querySelector('#recommendations');
const recommendationResults = document.querySelector('#recommendation-results');
const featuredBackdrop = document.querySelector('#featured-backdrop');
const movieDetailModal = document.querySelector('#movie-detail-modal');
const movieDetailContent = document.querySelector('#movie-detail-content');
const movieDetailClose = document.querySelector('#movie-detail-close');
const trailerModal = document.querySelector('#trailer-modal');
const trailerModalIframe = document.querySelector('#trailer-modal-iframe');
const trailerModalClose = document.querySelector('#trailer-modal-close');
const trendingSection = document.querySelector('#trending');
const trendingTrack = document.querySelector('#trending-track');
const trendingButtons = [...document.querySelectorAll('[data-trending-window]')];
const editorialFeature = document.querySelector('#editorial-feature');
const editorialBackdrop = document.querySelector('#editorial-backdrop');
const editorialTitle = document.querySelector('#editorial-title');
const editorialMeta = document.querySelector('#editorial-meta');
const editorialNote = document.querySelector('#editorial-note');
const editorialSaveActions = document.querySelector('#editorial-save-actions');
const surveyModal = document.querySelector('#survey-modal');
const surveyProgress = document.querySelector('#survey-progress');
const surveyTitle = document.querySelector('#survey-title');
const surveyQuestion = document.querySelector('#survey-question');
const surveyOptions = document.querySelector('#survey-options');
const surveyDemographics = document.querySelector('#survey-demographics');
const surveyAge = document.querySelector('#survey-age');
const genderOptions = document.querySelector('#gender-options');
const demographicsNext = document.querySelector('#survey-demographics-next');
const surveyResult = document.querySelector('#survey-result');
const surveyBox = document.querySelector('.survey-box');
const surveyClose = document.querySelector('#survey-close');
const mainPage = document.querySelector('#main-page');
const quizPage = document.querySelector('#quiz-page');
const quizHomeLink = document.querySelector('#quiz-home-link');
const quizChatNav = document.querySelector('#quiz-chat-nav');
const quizColumnNav = document.querySelector('#quiz-column-nav');
const columnPage = document.querySelector('#column-page');
const columnNav = document.querySelector('#column-nav');
const columnHome = document.querySelector('#column-home');
const columnQuizNav = document.querySelector('#column-quiz-nav');
const columnChatNav = document.querySelector('#column-chat-nav');
const chatPage = document.querySelector('#chat-page');
const chatNav = document.querySelector('#chat-nav');
const chatHome = document.querySelector('#chat-home');
const chatQuizNav = document.querySelector('#chat-quiz-nav');
const chatColumnNav = document.querySelector('#chat-column-nav');
const zodiacNav = document.querySelector('#zodiac-nav');
const zodiacResults = document.querySelector('#zodiac-results');
const zodiacLabel = document.querySelector('#zodiac-label');
const zodiacTitle = document.querySelector('#zodiac-title');
const zodiacCaption = document.querySelector('#zodiac-caption');
const zodiacWhy = document.querySelector('#zodiac-why');
const zodiacMovies = document.querySelector('#zodiac-movies');
const zodiacSelection = document.querySelector('#zodiac-selection');
const zodiacBack = document.querySelector('#zodiac-back');
const editorialColumns = document.querySelector('#editorial-columns');
const editorialCatalog = document.querySelector('#editorial-catalog');
const editorialResetPill = document.querySelector('#editorial-reset-pill');
const editorialHero = document.querySelector('#editorial-hero');
const editorialHeroQuick = document.querySelector('.editorial-hero-quick');
const featuredPoster = document.querySelector('#featured-poster');
const featuredTitle = document.querySelector('#featured-title');
const featuredMeta = document.querySelector('#featured-meta');
const featuredNote = document.querySelector('#featured-note');
const sourceButtons = [...document.querySelectorAll('[data-source]')];
let currentQuiz = null;
let selectedSource = 'tmdb';
let activeChatMovieId = null;
let activeChatMovieMeta = null;
let spoilerMode = false;
let chatMessages = [];
let chatIsLoading = false;
let chatFilmSearchTimer = null;
const CHAT_STORAGE_KEY = 'film-sitesi-top250-chat-v1';
const QUIZ_PROGRESS_KEY = 'sinequiz-rewards-v1';
const SURVEY_MOVIE_KEY = 'film-sitesi-anket-film-v1';
const SAVED_MOVIES_KEY = 'film-sitesi-saved-movies-v1';
const UI_PREFERENCES_KEY = 'film-sitesi-ui-preferences-v1';
const authState = { user: null, isAuthenticated: false, isLoading: true, csrfToken: null };

async function refreshAuthState() {
  try {
    const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
    const data = await response.json();
    authState.user = data.user || null;
    authState.isAuthenticated = Boolean(data.user);
    authState.csrfToken = data.csrfToken || null;
  } catch (_) {
    authState.user = null;
    authState.isAuthenticated = false;
    authState.csrfToken = null;
  } finally {
    authState.isLoading = false;
  }
  return authState;
}

const authReady = refreshAuthState();

async function authFetch(url, options = {}) {
  await authReady;
  const headers = new Headers(options.headers || {});
  if (authState.csrfToken) headers.set('X-CSRF-Token', authState.csrfToken);
  return fetch(url, { ...options, headers, credentials: 'same-origin' });
}
const QUIZ_BADGES = [
  { id: 'first-cut', icon: '✦', name: 'İlk Kare', unlocked: (progress) => progress.correct >= 1 },
  { id: 'poster-sleuth', icon: '▣', name: 'Afiş Avcısı', unlocked: (progress) => progress.posterCorrect >= 5 },
  { id: 'triple-take', icon: '⚡', name: 'Üçlü Seri', unlocked: (progress) => progress.bestCombo >= 3 },
  { id: 'reel-regular', icon: '◒', name: 'Perde Müdavimi', unlocked: (progress) => progress.total >= 25 },
];
let quizProgress = loadQuizProgress();
let quizStats = { correct: 0, incorrect: 0, total: 0, combo: 0, bestCombo: 0, xp: 0 };
const navigationCards = [...document.querySelectorAll('.topbar,.column-top')];

function loadUiPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem(UI_PREFERENCES_KEY) || '{}');
    return { motionEnabled: saved.motionEnabled !== false };
  } catch (_) {
    return { motionEnabled: true };
  }
}

let uiPreferences = loadUiPreferences();

function applyUiPreferences() {
  document.body.classList.toggle('settings-reduce-motion', !uiPreferences.motionEnabled);
}

applyUiPreferences();

function loadQuizProgress() {
  const empty = { xp: 0, total: 0, correct: 0, posterCorrect: 0, bestCombo: 0, sessions: 0, badges: [] };
  try {
    const saved = JSON.parse(localStorage.getItem(QUIZ_PROGRESS_KEY));
    if (!saved || typeof saved !== 'object') return empty;
    return { ...empty, ...saved, badges: Array.isArray(saved.badges) ? saved.badges : [] };
  } catch (_) {
    return empty;
  }
}

function saveQuizProgress() {
  localStorage.setItem(QUIZ_PROGRESS_KEY, JSON.stringify(quizProgress));
}

function renderQuizRewards() {
  if (quizXp) quizXp.textContent = quizProgress.xp;
  if (quizBadgeCount) quizBadgeCount.textContent = quizProgress.badges.length;
}

function recordQuizReward(correct, questionType) {
  quizStats.total += 1;
  quizProgress.total += 1;
  let earnedXp = 0;
  if (correct) {
    quizStats.correct += 1;
    quizProgress.correct += 1;
    quizStats.combo += 1;
    quizStats.bestCombo = Math.max(quizStats.bestCombo, quizStats.combo);
    quizProgress.bestCombo = Math.max(quizProgress.bestCombo, quizStats.combo);
    if (questionType === 'poster') quizProgress.posterCorrect += 1;
    earnedXp = 10 + Math.min((quizStats.combo - 1) * 5, 15) + (questionType === 'poster' ? 5 : 0);
    quizStats.xp += earnedXp;
    quizProgress.xp += earnedXp;
  } else {
    quizStats.incorrect += 1;
    quizStats.combo = 0;
  }
  const before = new Set(quizProgress.badges);
  const unlocked = QUIZ_BADGES.filter((badge) => badge.unlocked(quizProgress) && !before.has(badge.id));
  if (unlocked.length) quizProgress.badges = [...quizProgress.badges, ...unlocked.map((badge) => badge.id)];
  saveQuizProgress();
  renderQuizRewards();
  return { earnedXp, unlocked };
}

function setNavigationCollapsed(collapsed) {
  document.body.classList.toggle('nav-collapsed', collapsed);
  document.body.classList.toggle('nav-open', !collapsed);
  navigationCards.forEach((card) => {
    card.classList.toggle('is-collapsed', collapsed);
    const toggle = card.querySelector('.nav-toggle');
    toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.setAttribute('aria-label', collapsed ? 'Menüyü aç' : 'Menüyü kapat');
    toggle.textContent = collapsed ? '☰' : '‹';
  });
}

navigationCards.forEach((card) => card.querySelector('.nav-toggle').addEventListener('click', () => {
  setNavigationCollapsed(!card.classList.contains('is-collapsed'));
}));
setNavigationCollapsed(true);

(function initNavAttentionHint() {
  const HINT_KEY = 'navHintShown';
  let alreadyShown = false;
  try { alreadyShown = sessionStorage.getItem(HINT_KEY) === '1'; } catch (_) { alreadyShown = false; }
  if (alreadyShown) return;
  const card = navigationCards[0];
  const toggle = card?.querySelector('.nav-toggle');
  const tooltip = document.querySelector('#nav-hint-tooltip');
  if (!card || !toggle) return;
  let done = false;
  function markSeen() {
    if (done) return;
    done = true;
    try { sessionStorage.setItem(HINT_KEY, '1'); } catch (_) { /* private mode: skip persisting */ }
    toggle.classList.remove('nav-hint-nudge');
    tooltip?.classList.remove('visible');
  }
  setTimeout(() => {
    if (!card.classList.contains('is-collapsed')) { markSeen(); return; }
    toggle.classList.add('nav-hint-nudge');
    tooltip?.classList.add('visible');
    setTimeout(() => tooltip?.classList.remove('visible'), 2600);
    setTimeout(markSeen, 3000);
  }, 1000);
  toggle.addEventListener('click', markSeen, { once: true });
})();

function setSelectedSource(source) {
  selectedSource = source;
  sourceButtons.forEach((item) => item.classList.toggle('active', item.dataset.source === source));
}

sourceButtons.forEach((item) => item.addEventListener('click', () => setSelectedSource(item.dataset.source)));

const soundToggle = document.querySelector('.sound-toggle');
soundToggle?.addEventListener('click', () => {
  const isOn = soundToggle.getAttribute('aria-pressed') === 'true';
  soundToggle.setAttribute('aria-pressed', String(!isOn));
  soundToggle.lastChild.textContent = !isOn ? ' Ambiyans açık' : ' Ambiyans kapalı';
});

surveyClose?.addEventListener('click', () => {
  surveyModal.hidden = true;
  queueHeroInfoAfterSurveyClose();
});

function posterFor(movie) {
  const genres = (movie.genres || []).join(' ').toLowerCase();
  if (genres.includes('animasyon') || genres.includes('aile')) return '/static/images/trivia-tv.png';
  if (genres.includes('romantik') || genres.includes('komedi')) return '/static/images/trivia-music.png';
  return '/static/images/trivia-film.png';
}

const savedMovieRegistry = new Map();
// Eski guest localStorage kaydı silinmez; aktif hesap listeleri yalnızca backend'den gelir.
let savedMoviesState = emptySavedMoviesState();
let savedMovieToastTimer = null;

function emptySavedMoviesState() {
  return { favorites: {}, watchlist: {} };
}

function loadSavedMovies() {
  try {
    const saved = JSON.parse(localStorage.getItem(SAVED_MOVIES_KEY));
    if (!saved || typeof saved !== 'object') return emptySavedMoviesState();
    return {
      favorites: saved.favorites && typeof saved.favorites === 'object' ? saved.favorites : {},
      watchlist: saved.watchlist && typeof saved.watchlist === 'object' ? saved.watchlist : {},
    };
  } catch (_) {
    return emptySavedMoviesState();
  }
}

function normalizeSavedMovie(movie) {
  return {
    id: movie.id,
    title: movie.title || 'İsimsiz film',
    year: movie.year || '—',
    genres: Array.isArray(movie.genres) ? movie.genres : [],
    rating: movie.rating || null,
    poster_url: movie.poster_url || posterFor(movie),
    backdrop_url: movie.backdrop_url || '',
    overview: movie.overview || movie.note || '',
    source: movie.source || 'TMDB Güncel Katalog',
  };
}

function registerSavedMovie(movie) {
  if (movie?.id !== undefined && movie?.id !== null) {
    savedMovieRegistry.set(String(movie.id), normalizeSavedMovie(movie));
  }
  return movie;
}

function savedMovieIcon(list) {
  if (list === 'favorites') {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.7a5.5 5.5 0 0 0-7.8 0L12 5.8l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.7-7.5 1.1-1.1a5.5 5.5 0 0 0 0-7.7Z"/></svg>';
  }
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11v17L12 17l-5.5 3.5v-17Z"/></svg>';
}

function trailerButtonIcon() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5-11-6.5Z"/></svg>';
}

function isMovieSaved(list, movieId) {
  return Boolean(savedMoviesState[list]?.[String(movieId)]);
}

function movieSaveActionsHtml(movie, extraClass = '') {
  registerSavedMovie(movie);
  const movieId = escapeHtml(String(movie.id));
  const favoriteActive = isMovieSaved('favorites', movie.id);
  const watchlistActive = isMovieSaved('watchlist', movie.id);
  return `<span class="movie-save-actions ${extraClass}" aria-label="Film listeleri">
    <button class="movie-save-action" type="button" data-trailer-movie-id="${movieId}" aria-label="Fragmanı izle" title="Fragmanı izle">${trailerButtonIcon()}</button>
    <button class="movie-save-action${favoriteActive ? ' is-active' : ''}" type="button" data-save-list="favorites" data-save-movie-id="${movieId}" aria-pressed="${favoriteActive}" aria-label="${favoriteActive ? 'Favorilerden çıkar' : 'Favorilere ekle'}" title="${favoriteActive ? 'Favorilerden çıkar' : 'Favorilere ekle'}">${savedMovieIcon('favorites')}</button>
    <button class="movie-save-action${watchlistActive ? ' is-active' : ''}" type="button" data-save-list="watchlist" data-save-movie-id="${movieId}" aria-pressed="${watchlistActive}" aria-label="${watchlistActive ? 'İzleme listesinden çıkar' : 'İzleme listesine ekle'}" title="${watchlistActive ? 'İzleme listesinden çıkar' : 'İzleme listesine ekle'}">${savedMovieIcon('watchlist')}</button>
  </span>`;
}

function syncSavedMovieControls() {
  document.querySelectorAll('.movie-save-action[data-save-list][data-save-movie-id]').forEach((control) => {
    const active = isMovieSaved(control.dataset.saveList, control.dataset.saveMovieId);
    const favorite = control.dataset.saveList === 'favorites';
    const label = active
      ? (favorite ? 'Favorilerden çıkar' : 'İzleme listesinden çıkar')
      : (favorite ? 'Favorilere ekle' : 'İzleme listesine ekle');
    control.classList.toggle('is-active', active);
    control.setAttribute('aria-pressed', String(active));
    control.setAttribute('aria-label', label);
    control.title = label;
  });
}

function showSavedMovieToast(message) {
  let toast = document.querySelector('#movie-save-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'movie-save-toast';
    toast.className = 'movie-save-toast';
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('is-visible');
  clearTimeout(savedMovieToastTimer);
  savedMovieToastTimer = setTimeout(() => toast.classList.remove('is-visible'), 1800);
}

const AUTH_SAVE_MODAL_DEFAULT_COPY = {
  title: 'Bu filmi kaydetmek ister misin?',
  description: 'Favorilerini ve izleme listeni saklamak için giriş yap veya hesap oluştur.',
};

// Aynı guest auth-gate modalı favoriler/izleme listesi VE blog "Yazı Yaz" aksiyonu
// için reuse edilir — copy parametreyle değişir, ikinci bir modal oluşturulmaz.
function openAuthSaveModal(copy = AUTH_SAVE_MODAL_DEFAULT_COPY) {
  const modal = document.querySelector('#auth-save-modal');
  if (!modal) return;
  const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  const encodedNext = encodeURIComponent(next);
  const loginLink = document.querySelector('#auth-save-login');
  const registerLink = document.querySelector('#auth-save-register');
  const titleEl = document.querySelector('#auth-save-title');
  const descriptionEl = modal.querySelector('.auth-modal-card p');
  if (titleEl) titleEl.textContent = copy.title;
  if (descriptionEl) descriptionEl.textContent = copy.description;
  if (loginLink) loginLink.href = `/giris?next=${encodedNext}`;
  if (registerLink) registerLink.href = `/uye-ol?next=${encodedNext}`;
  modal.hidden = false;
  modal.querySelector('#auth-save-close')?.focus();
}

function closeAuthSaveModal() {
  const modal = document.querySelector('#auth-save-modal');
  if (modal) modal.hidden = true;
}

async function toggleSavedMovie(list, movieId) {
  if (!['favorites', 'watchlist'].includes(list)) return;
  await authReady;
  if (!authState.isAuthenticated) {
    openAuthSaveModal();
    return;
  }
  const id = String(movieId);
  const wasSaved = isMovieSaved(list, id);
  const movie = savedMovieRegistry.get(id)
    || savedMoviesState.favorites[id]
    || savedMoviesState.watchlist[id];
  if (!movie) return;
  try {
    const response = await authFetch(
      wasSaved ? `/api/user/movies/${list}/${encodeURIComponent(id)}` : `/api/user/movies/${list}`,
      wasSaved
        ? { method: 'DELETE' }
        : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ movie }) }
    );
    const data = await response.json();
    if (response.status === 401) {
      authState.user = null;
      authState.isAuthenticated = false;
      openAuthSaveModal();
      return;
    }
    if (!response.ok) throw new Error(data.error || 'Film kaydedilemedi.');
    if (wasSaved) delete savedMoviesState[list][id];
    else savedMoviesState[list][id] = normalizeSavedMovie(data.movie || movie);
  } catch (error) {
    showSavedMovieToast(error.message);
    return;
  }
  syncSavedMovieControls();
  renderSavedMoviesPage();
  const message = list === 'favorites'
    ? (wasSaved ? 'Favorilerden çıkarıldı.' : 'Favorilere eklendi.')
    : (wasSaved ? 'İzleme listesinden çıkarıldı.' : 'İzleme listesine eklendi.');
  showSavedMovieToast(message);
}

async function handleMovieSaveAction(event) {
  const action = event.target.closest?.('.movie-save-action[data-save-list][data-save-movie-id]');
  if (!action) return;
  event.preventDefault();
  event.stopPropagation();
  await toggleSavedMovie(action.dataset.saveList, action.dataset.saveMovieId);
}

// Capture aşamasında durdurulur; kalp/yer imi kartın film detayı aksiyonunu tetiklemez.
document.addEventListener('click', handleMovieSaveAction, true);

// ===== Fragman: kart üzerindeki ▶ butonu, TMDB /movie/{id}/videos'u yalnızca =====
// tıklanınca (lazy) çeker; aynı film için tekrar tıklamada sonucu bellekte önbellekler. =====
const trailerKeyCache = new Map();

function openTrailerModal(key) {
  if (!trailerModal || !trailerModalIframe) return;
  trailerModalIframe.src = `https://www.youtube.com/embed/${encodeURIComponent(key)}?autoplay=1&rel=0`;
  trailerModal.hidden = false;
  document.body.classList.add('detail-open');
}

function closeTrailerModal() {
  if (!trailerModal) return;
  trailerModal.hidden = true;
  if (trailerModalIframe) trailerModalIframe.src = '';
  if (!movieDetailModal || movieDetailModal.hidden) document.body.classList.remove('detail-open');
}

async function handleTrailerButtonClick(event) {
  const button = event.target.closest?.('[data-trailer-movie-id]');
  if (!button) return;
  event.preventDefault();
  event.stopPropagation();
  if (button.classList.contains('is-unavailable') || button.classList.contains('is-loading')) return;
  const movieId = button.dataset.trailerMovieId;
  if (trailerKeyCache.has(movieId)) {
    const cachedKey = trailerKeyCache.get(movieId);
    if (cachedKey) openTrailerModal(cachedKey);
    return;
  }
  button.classList.add('is-loading');
  try {
    const response = await fetch(`/api/movie/${movieId}/trailer`);
    const data = await response.json();
    const key = response.ok ? data.key || null : null;
    trailerKeyCache.set(movieId, key);
    if (key) {
      openTrailerModal(key);
    } else {
      button.classList.add('is-unavailable');
      button.title = 'Bu film için fragman bulunamadı.';
      button.setAttribute('aria-label', 'Fragman bulunamadı');
      showSavedMovieToast('Bu film için fragman bulunamadı.');
    }
  } catch (error) {
    showSavedMovieToast('Fragman yüklenemedi.');
  } finally {
    button.classList.remove('is-loading');
  }
}

document.addEventListener('click', handleTrailerButtonClick, true);
trailerModalClose?.addEventListener('click', closeTrailerModal);
trailerModal?.querySelector('[data-trailer-close]')?.addEventListener('click', closeTrailerModal);

window.addEventListener('storage', (event) => {
  if (event.key !== SAVED_MOVIES_KEY) return;
  // Guest kayıtları ilk sürümde hesaba otomatik aktarılmaz; veri yerinde korunur.
});

document.querySelector('#auth-save-close')?.addEventListener('click', closeAuthSaveModal);
document.querySelector('#auth-save-modal')?.addEventListener('click', (event) => {
  if (event.target.id === 'auth-save-modal') closeAuthSaveModal();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeAuthSaveModal();
});

const zodiacCopy = {
  'Koç': ['Cesur ve temposu yüksek.', 'Harekete geçiren, enerjini taşıyacak hikâyeler.'],
  'Boğa': ['Yavaşla, keyfine bak.', 'Sıcak, sakin ve görsel dünyası güçlü filmler.'],
  'İkizler': ['Merakın yönü sürekli değişsin.', 'Zekice oyunlar ve sürprizler sevenler için.'],
  'Yengeç': ['Kalbe iyi gelen hikâyeler.', 'Aile, dostluk ve tanıdık duyguların peşinde.'],
  'Aslan': ['Işığı biraz üzerine çek.', 'Büyük duygular, büyük sahneler ve ilham veren karakterler.'],
  'Başak': ['Detaylarda kaybolmak serbest.', 'İncelikli kurgu ve güçlü atmosfer bu seçkinin odağında.'],
  'Terazi': ['Zarafet de bir ruh hali.', 'Romantizm, stil ve hafiflik arasında dengeli bir gece.'],
  'Akrep': ['Gecenin biraz daha karanlık yüzü.', 'Gerilim, sır ve yoğun karakterlerle dolu hikâyeler.'],
  'Yay': ['Ufku genişleten bir gece.', 'Yolculuk, macera ve özgürlük hissi taşıyan filmler.'],
  'Oğlak': ['Sakin bir kararlılıkla izle.', 'Emek, hedef ve dönüşüm anlatan güçlü karakter öyküleri.'],
  'Kova': ['Alışılmadık olana yer aç.', 'Farklı fikirler ve geleceğe dönük dünyalar için bir seçki.'],
  'Balık': ['Biraz hayal, biraz şiir.', 'Duygusal ve düşsel bir akşama eşlik edecek filmler.']
};

const zodiacWhyCopy = {
  'Koç': ['Koç enerjisi durup düşünmekten çok harekete geçmeyi sever; bu seçki sana yüksek tempo ve cesur kararlar bırakıyor.', ['Seni ilk dakikada hikâyenin içine çeker.', 'Enerjini düşürmeden sürprizler sunar.', 'Güçlü karakterlerin risk alma cesaretine eşlik eder.']],
  'Boğa': ['Boğa için iyi bir film, acele ettirmeden içine alan ve sonunda sıcaklık bırakan filmdir; bu seçki tam o gece için.', ['Görsel dünyasıyla küçük bir keyif alanı açar.', 'Rahat bir ritimle sana nefes aldırır.', 'Konfor hissini güçlü bir hikâyeyle buluşturur.']],
  'İkizler': ['İkizler merakı canlı tutan, yön değiştiren hikâyeleri sever; bu filmlerde her an yeni bir fikir var.', ['Zihnini meşgul eden küçük oyunlar taşır.', 'Tahmin etmesi zor dönüşlerle seni canlı tutar.', 'Konuşacak yeni bir detay bırakır.']],
  'Yengeç': ['Yengeç için en iyi seçki, duygusu gerçek gelen ve bağ kurabileceği karakterler taşıyandır.', ['Duygusal bağ kurabileceğin bir dünya yaratır.', 'Kalbe yakın, tanıdık bir sıcaklık sunar.', 'Film bittikten sonra da yanında kalır.']],
  'Aslan': ['Aslan enerjisi için perde biraz daha büyük açılmalı; bu seçkide ilham, tutku ve güçlü sahneler var.', ['Sana büyük bir hikâyenin parçasıymışsın hissi verir.', 'Tutkulu karakterleriyle ilham taşır.', 'Işığını kaybetmeyen bir enerji sunar.']],
  'Başak': ['Başak, iyi kurulmuş ayrıntıları ve ince işçiliği fark eder; bu filmler gözden kaçan detaylarıyla ödüllendirir.', ['İncelikli yapısıyla dikkatini canlı tutar.', 'Her sahnesinde küçük bir ipucu saklar.', 'Düzenli kurgusuyla tatmin edici bir akış sunar.']],
  'Terazi': ['Terazi için seçim hem hissettirmeli hem de güzel görünmeli; bu filmler stil ve duyguyu dengeliyor.', ['Zarif atmosferiyle seni içine çeker.', 'Duygu ve estetiği dengede tutar.', 'İzlemesi kadar konuşması da keyifli bir tat bırakır.']],
  'Akrep': ['Akrep enerjisi yüzeyde kalmayan hikâyeleri sever; bu seçkide sırlar, gerilim ve yoğunluk var.', ['İçinde sakladığı sırlarla merakını besler.', 'Karanlık atmosferiyle güçlü bir iz bırakır.', 'Karakterlerin derinliğine inmeni sağlar.']],
  'Yay': ['Yay için iyi film, yeni bir yere götüren filmdir; bu seçki macera, hareket ve özgürlük hissi taşıyor.', ['Sana yeni bir dünyanın kapısını açar.', 'Özgürlük duygusunu taze tutar.', 'Macera hissini son ana kadar taşır.']],
  'Oğlak': ['Oğlak, emeğin ve dönüşümün karşılığını görmek ister; bu filmler hedefi olan karakterlerle ilerliyor.', ['Kararlı karakterlerin gücünü hatırlatır.', 'Emek ve dönüşüm temasını taşır.', 'Sonunda hak edilmiş bir tatmin bırakır.']],
  'Kova': ['Kova için sıradan olmayan fikirler daha heyecanlıdır; bu seçki bakış açını biraz yerinden oynatacak.', ['Alışılmadık fikriyle merak uyandırır.', 'Farklı bir dünyanın kurallarını keşfettirir.', 'Zihninde yeni bir soru bırakır.']],
  'Balık': ['Balık, gerçekliğin biraz yumuşadığı hikâyelerde iyi hisseder; bu seçki hayal gücüne alan açıyor.', ['Hayal gücüne yumuşak bir alan açar.', 'Duygusal tonuyla sana eşlik eder.', 'Gerçeklikten nazikçe uzaklaştırır.']]
};


function showColumnPage() {
  mainPage.hidden = true;
  quizPage.hidden = true;
  chatPage.hidden = true;
  columnPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function hideColumnPage() {
  columnPage.hidden = true;
  mainPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showChatPage() {
  mainPage.hidden = true;
  quizPage.hidden = true;
  columnPage.hidden = true;
  chatPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function hideChatPage() {
  chatPage.hidden = true;
  mainPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showQuizPage() {
  mainPage.hidden = true;
  columnPage.hidden = true;
  chatPage.hidden = true;
  quizPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'auto' });
}

function hideQuizPage() {
  quizPage.hidden = true;
  mainPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showMainPage() {
  quizPage.hidden = true;
  columnPage.hidden = true;
  chatPage.hidden = true;
  mainPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadZodiac(zodiac) {
  zodiacResults.hidden = false;
  const [title, caption] = zodiacCopy[zodiac];
  zodiacLabel.textContent = `${zodiac.toUpperCase()} İÇİN FİLM GECESİ`;
  zodiacTitle.textContent = title;
  zodiacCaption.textContent = caption;
  zodiacWhy.innerHTML = `<strong>Neden ${zodiac}?</strong> ${zodiacWhyCopy[zodiac][0]}`;
  zodiacNav.querySelectorAll('button').forEach((item) => item.classList.toggle('active', item.dataset.zodiac === zodiac));
  zodiacMovies.innerHTML = '<p class="column-loading">Seçki hazırlanıyor…</p>';
  try {
    const response = await fetch('/api/zodiac-recommend', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ zodiac })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Seçki hazırlanamadı.');
    zodiacMovies.innerHTML = data.movies.map((movie, index) => `<article class="column-movie" data-movie-id="${movie.id}" role="button" tabindex="0" aria-label="${escapeHtml(movie.title)} film ayrıntılarını aç"><span class="movie-card-media"><img src="${movie.poster_url || posterFor(movie)}" alt="${escapeHtml(movie.title)} afişi" />${movieSaveActionsHtml(movie)}</span><div class="column-movie-copy"><h3>${escapeHtml(movie.title)}</h3><p class="column-meta">${escapeHtml(movie.year)} · ${escapeHtml(movie.genres.join(' · '))}${movie.rating ? ` · TMDB ${Number(movie.rating).toFixed(1)}` : ''}</p><span class="source-badge">${escapeHtml(movie.source || 'TMDB Güncel Katalog')}</span><p class="column-match">${escapeHtml(zodiacWhyCopy[zodiac][1][index % zodiacWhyCopy[zodiac][1].length])}</p><span class="column-open-hint">AYRINTILARI GÖR →</span></div></article>`).join('');
  } catch (error) {
    zodiacMovies.innerHTML = '<p class="column-loading">' + escapeHtml(error.message) + '</p>';
  }
}

let selectedEditorial = null;

// Slug -> ilgili 3 köşe yazısı. Ruh haline yakın kategorileri birbirine
// bağlar; her yazının sonundaki "Şimdi bunlara da göz at" alanı bunu kullanır.
const EDITORIAL_RELATED = {
  'yorgun-aksam': ['hayatini-toparlama', 'yagmurlu-pazar', 'arkadaslarla-gece'],
  'ilk-15-dakika': ['ters-gidecek-his', 'gece-yarisi', 'kesif-hazine'],
  'gece-yarisi': ['ters-gidecek-his', 'ilk-15-dakika', 'kesif-hazine'],
  'arkadaslarla-gece': ['yorgun-aksam', 'klise-olmayan-ask', 'hayatini-toparlama'],
  'klise-olmayan-ask': ['yagmurlu-pazar', 'hayatini-toparlama', 'arkadaslarla-gece'],
  'ters-gidecek-his': ['gece-yarisi', 'ilk-15-dakika', 'kesif-hazine'],
  'hayatini-toparlama': ['yagmurlu-pazar', 'yorgun-aksam', 'klise-olmayan-ask'],
  'yagmurlu-pazar': ['hayatini-toparlama', 'klise-olmayan-ask', 'yorgun-aksam'],
  'kesif-hazine': ['gece-yarisi', 'ters-gidecek-his', 'ilk-15-dakika'],
};

function syncEditorialActiveState() {
  document.querySelectorAll('.editorial-quick-pill[data-column-slug]').forEach((el) => {
    el.classList.toggle('active', selectedEditorial !== null && el.dataset.columnSlug === selectedEditorial);
  });
  editorialResetPill?.classList.toggle('active', selectedEditorial === null);
}

function scrollToEditorialSection(element) {
  if (!element) return;
  const desiredOffset = window.innerWidth <= 640 ? 44 : 64;
  // Hidden/visible section değişiminin layout'a yansımasını bekleyip gerçek
  // document konumunu ölç; böylece hero'nun alt kenarı viewport'ta kalmaz.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const y = element.getBoundingClientRect().top + window.pageYOffset - desiredOffset;
      window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
    });
  });
}

function hideZodiacSections() {
  if (zodiacSelection) zodiacSelection.hidden = true;
  if (zodiacResults) zodiacResults.hidden = true;
}

function showZodiacSelection() {
  hideZodiacSections();
  if (zodiacSelection) zodiacSelection.hidden = false;
  loadZodiac('Koç');
}

function editorialPathFor(slug) {
  return slug ? `/kose-yazisi/${slug}` : '/kose-yazisi';
}

function renderEditorialRelated(slug) {
  const wrap = document.querySelector(`.editorial-related[data-related-for="${slug}"]`);
  const grid = wrap?.querySelector('.editorial-related-grid');
  if (!wrap || !grid) return;
  const relatedSlugs = EDITORIAL_RELATED[slug] || [];
  if (!relatedSlugs.length) { wrap.hidden = true; return; }
  grid.innerHTML = relatedSlugs.map((relSlug) => {
    const sourceCard = document.querySelector(`.editorial-catalog-card[data-column-slug="${relSlug}"]`);
    if (!sourceCard) return '';
    const imgSrc = sourceCard.querySelector('img')?.getAttribute('src') || '';
    const label = sourceCard.querySelector('.editorial-catalog-label')?.textContent || '';
    const title = sourceCard.querySelector('.editorial-catalog-title')?.textContent || '';
    return `<button class="editorial-related-card" type="button" data-column-slug="${relSlug}"><span class="editorial-related-media">${imgSrc ? `<img src="${imgSrc}" alt="" loading="lazy" />` : ''}</span><span class="editorial-related-copy"><span class="editorial-related-label">${escapeHtml(label)}</span><span class="editorial-related-title">${escapeHtml(title)}</span></span></button>`;
  }).join('');
  wrap.hidden = false;
}

async function loadEditorialSectionMovies(slug, container) {
  try {
    const response = await fetch('/api/column-recommend', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slug })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Köşe yazısı hazırlanamadı.');
    container.innerHTML = data.movies.map((movie, index) => `<article class="column-movie" data-movie-id="${movie.id}" role="button" tabindex="0" aria-label="${escapeHtml(movie.title)} film ayrıntılarını aç"><span class="column-index">${String(index + 1).padStart(2, '0')}</span><span class="movie-card-media"><img src="${movie.poster_url || posterFor(movie)}" alt="${escapeHtml(movie.title)} afişi" />${movieSaveActionsHtml(movie)}</span><div class="column-movie-copy"><h3>${escapeHtml(movie.title)}</h3><p class="column-meta">${escapeHtml(movie.year)} · ${escapeHtml(movie.genres.join(' · '))}${movie.rating ? ` · TMDB ${Number(movie.rating).toFixed(1)}` : ''}</p><span class="source-badge">${escapeHtml(movie.source || 'TMDB Güncel Katalog')}</span><p class="column-match">${escapeHtml(data.why[index % data.why.length])}</p><span class="column-open-hint">Filmi keşfet →</span></div></article>`).join('');
    container.dataset.loaded = '1';
  } catch (error) {
    container.innerHTML = '<p class="column-loading">' + escapeHtml(error.message) + '</p>';
  }
}

// Katalogdan/hızlı seçimden gelen slug'ı uygular: yalnızca ilgili köşe
// yazısını gösterir, diğer 9'u DOM'da gizli ve yüklenmemiş kalır.
function applyEditorialSelection(slug) {
  selectedEditorial = slug;
  columnPage?.classList.toggle('editorial-detail-page', !!slug);
  columnPage?.classList.toggle('editorial-landing-page', !slug);
  if (editorialHero) editorialHero.hidden = !!slug;
  syncEditorialActiveState();
  if (editorialCatalog) editorialCatalog.hidden = !!slug;

  if (slug === 'zodiac') {
    if (editorialColumns) editorialColumns.hidden = true;
    document.querySelectorAll('.editorial-section').forEach((section) => { section.hidden = true; });
    showZodiacSelection();
    return;
  }

  hideZodiacSections();
  if (!slug) {
    if (editorialColumns) editorialColumns.hidden = true;
    return;
  }

  if (editorialColumns) editorialColumns.hidden = false;
  document.querySelectorAll('.editorial-section').forEach((section) => {
    section.hidden = section.dataset.columnSlug !== slug;
  });
  const container = document.querySelector(`.column-movies[data-movies-for="${slug}"]`);
  if (container && container.dataset.loaded !== '1') loadEditorialSectionMovies(slug, container);
  renderEditorialRelated(slug);
}

// Hızlı seçim kutuları ve katalog kartları aynı işi yapar: seçilen köşe
// yazısının detayını açar, diğerleri gizli kalır (bir filtre değil, navigasyon).
function selectEditorial(slug) {
  const previousSlug = selectedEditorial;
  applyEditorialSelection(slug);
  if (previousSlug !== slug) history.pushState({ editorialSlug: slug }, '', editorialPathFor(slug));
  scrollToEditorialSection(slug === 'zodiac' ? zodiacSelection : document.querySelector(`#editorial-section-${slug}`));
}

function clearEditorialSelection() {
  if (!editorialHero) {
    window.location.assign(editorialPathFor(null));
    return;
  }
  const previousSlug = selectedEditorial;
  applyEditorialSelection(null);
  if (previousSlug !== null) history.pushState({ editorialSlug: null }, '', editorialPathFor(null));
  scrollToEditorialSection(editorialCatalog);
}

async function loadEditorialPreviews() {
  if (!editorialCatalog) return;
  try {
    const response = await fetch('/api/column-previews');
    const data = await response.json();
    const previews = data.previews || {};
    Object.entries(previews).forEach(([slug, preview]) => {
      const card = editorialCatalog?.querySelector(`.editorial-catalog-card[data-column-slug="${slug}"]`);
      const img = card?.querySelector('[data-preview-img]');
      if (img && (preview.backdropUrl || preview.posterUrl)) {
        img.src = preview.backdropUrl || preview.posterUrl;
        img.alt = preview.title ? `${preview.title} afişi` : '';
      }
    });
    // İlk yüklemede bir köşe yazısı zaten açık olabilir (doğrudan URL ile
    // gelinmiş) — önizleme görselleri geldikten sonra "göz at" kartlarını tazele.
    if (selectedEditorial && selectedEditorial !== 'zodiac') renderEditorialRelated(selectedEditorial);
  } catch (_) {
    // Önizleme görselleri olmadan da katalog ve ilgili yazılar okunur kalır.
  }
}

editorialHeroQuick?.addEventListener('click', (event) => {
  if (event.target.closest('#editorial-reset-pill')) { clearEditorialSelection(); return; }
  const pill = event.target.closest('.editorial-quick-pill[data-column-slug]');
  if (pill) selectEditorial(pill.dataset.columnSlug);
});

editorialCatalog?.addEventListener('click', (event) => {
  const card = event.target.closest('.editorial-catalog-card[data-column-slug]');
  if (card) selectEditorial(card.dataset.columnSlug);
});

zodiacBack?.addEventListener('click', clearEditorialSelection);

editorialColumns?.addEventListener('click', (event) => {
  if (event.target.closest('#editorial-columns-back')) { clearEditorialSelection(); return; }
  const relatedCard = event.target.closest('.editorial-related-card[data-column-slug]');
  if (relatedCard) { selectEditorial(relatedCard.dataset.columnSlug); return; }
  const card = event.target.closest('.column-movie[data-movie-id]');
  if (card) openMovieDetails(card.dataset.movieId);
});
editorialColumns?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  const card = event.target.closest('.column-movie[data-movie-id]');
  if (!card) return;
  event.preventDefault();
  openMovieDetails(card.dataset.movieId);
});

function parseEditorialSlugFromPath() {
  const match = location.pathname.match(/^\/kose-yazisi\/([^/]+)\/?$/);
  return match ? decodeURIComponent(match[1]) : null;
}

if (columnPage) {
  const initialEditorialSlug = window.__EDITORIAL_INITIAL_SLUG__ || null;
  history.replaceState({ editorialSlug: initialEditorialSlug }, '', location.pathname);
  applyEditorialSelection(initialEditorialSlug);

  window.addEventListener('popstate', (event) => {
    const slug = event.state ? event.state.editorialSlug : parseEditorialSlugFromPath();
    if (!slug && !editorialHero) {
      window.location.replace(editorialPathFor(null));
      return;
    }
    applyEditorialSelection(slug || null);
    const target = slug === 'zodiac' ? zodiacSelection : slug ? document.querySelector(`#editorial-section-${slug}`) : editorialCatalog;
    target?.scrollIntoView({ block: 'start' });
  });
}

loadEditorialPreviews();

zodiacNav?.addEventListener('click', (event) => {
  const zodiac = event.target.closest('[data-zodiac]')?.dataset.zodiac;
  if (zodiac) loadZodiac(zodiac);
});

zodiacMovies?.addEventListener('click', (event) => {
  const card = event.target.closest('.column-movie[data-movie-id]');
  if (card) openMovieDetails(card.dataset.movieId);
});
zodiacMovies?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  const card = event.target.closest('.column-movie[data-movie-id]');
  if (!card) return;
  event.preventDefault();
  openMovieDetails(card.dataset.movieId);
});

function updateFeatured(movie) {
  if (!movie || !featuredPoster) return;
  featuredPoster.src = movie.poster_url || posterFor(movie);
  featuredPoster.alt = movie.title;
  featuredTitle.textContent = movie.title;
  featuredMeta.textContent = `${movie.year} · ${movie.genres.join(' · ')}`;
  featuredNote.textContent = movie.note;
}

// Hero backdrop: anket sonucu varsa ilk slide o film olur, ardından TMDB trend
// listesiyle rotasyon kesintisiz sürer; 10sn'de bir soft-crossfade ile döner.
const HERO_ROTATE_MS = 10000;
const heroInfo = document.querySelector('#hero-info');
const heroInfoToggle = document.querySelector('#hero-info-toggle');
const heroInfoCard = document.querySelector('#hero-info-card');
const heroInfoLink = document.querySelector('#hero-info-link');
const heroInfoPosterImg = document.querySelector('#hero-info-poster-img');
const heroInfoTitle = document.querySelector('#hero-info-title');
const heroInfoMeta = document.querySelector('#hero-info-meta');
const heroInfoOverview = document.querySelector('#hero-info-overview');
const heroInfoSaveActions = document.querySelector('#hero-info-save-actions');
let heroInfoCurrentMovie = null;
let heroLayerEls = featuredBackdrop ? [...featuredBackdrop.querySelectorAll('[data-hero-layer]')] : [];
let heroActiveLayerIndex = 0;
let heroMovies = [];
let heroIndex = 0;
let heroTimer = null;
let heroInfoAutoCloseTimer = null;
let heroInfoAutoShowActive = false;
let heroInfoManuallyOpen = false;
const HERO_INFO_AUTO_VISIBLE_MS = 1000;

function heroImageUrl(movie) {
  return (movie && (movie.backdrop_url || movie.poster_url)) || '';
}

function preloadHeroImage(url) {
  if (!url) return;
  const img = new Image();
  img.src = url;
}

function stopHeroRotation() {
  if (heroTimer) { clearInterval(heroTimer); heroTimer = null; }
}

function showHeroMovie(movie) {
  const url = heroImageUrl(movie);
  if (!url || heroLayerEls.length < 2) return;
  const nextIndex = (heroActiveLayerIndex + 1) % 2;
  const nextLayer = heroLayerEls[nextIndex];
  const currentLayer = heroLayerEls[heroActiveLayerIndex];
  nextLayer.style.backgroundImage = `url("${url}")`;
  requestAnimationFrame(() => {
    nextLayer.classList.add('active');
    currentLayer.classList.remove('active');
  });
  heroActiveLayerIndex = nextIndex;
  updateHeroInfoCard(movie);
}

function updateHeroInfoCard(movie) {
  heroInfoCurrentMovie = movie;
  if (!movie || !heroInfoTitle) return;
  if (heroInfoPosterImg) {
    heroInfoPosterImg.src = movie.poster_url || posterFor(movie);
    heroInfoPosterImg.alt = `${movie.title} afişi`;
  }
  heroInfoTitle.textContent = movie.title;
  if (heroInfoMeta) {
    const rating = movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : '';
    const genres = Array.isArray(movie.genres) ? movie.genres.slice(0, 2).join(' · ') : '';
    heroInfoMeta.textContent = `${movie.year}${genres ? ' · ' + genres : ''}${rating}`;
  }
  if (heroInfoOverview) {
    heroInfoOverview.textContent = String(movie.overview || movie.note || 'Kısa konu bilgisi bulunmuyor.').trim();
  }
  if (heroInfoSaveActions) heroInfoSaveActions.innerHTML = movieSaveActionsHtml(movie);
  maybeAutoShowHeroInfo();
}

function clearHeroInfoTimers() {
  clearTimeout(heroInfoAutoCloseTimer);
  heroInfoAutoCloseTimer = null;
}

function openHeroInfoCard({ manual = false } = {}) {
  if (!heroInfoCard || !heroInfoCurrentMovie) return;
  clearHeroInfoTimers();
  heroInfoAutoShowActive = false;
  heroInfoManuallyOpen = manual;
  heroInfoCard.classList.add('visible');
  heroInfoToggle?.setAttribute('aria-expanded', 'true');
}

function closeHeroInfoCard() {
  clearHeroInfoTimers();
  heroInfoAutoShowActive = false;
  heroInfoManuallyOpen = false;
  heroInfoCard?.classList.remove('visible');
  heroInfoToggle?.setAttribute('aria-expanded', 'false');
}

let heroInfoSurveyClosed = !surveyModal || surveyModal.hidden;

function queueHeroInfoAfterSurveyClose() {
  heroInfoSurveyClosed = true;
  // Anketi kapatan click önce document seviyesindeki kapatma dinleyicisini
  // tamamlasın; bilgi kartı sonraki frame'de güvenle açılsın.
  setTimeout(maybeAutoShowHeroInfo, 120);
}

function maybeAutoShowHeroInfo() {
  if (!heroInfoSurveyClosed || !heroInfoCurrentMovie || !heroInfoCard || heroInfoManuallyOpen) return;
  clearHeroInfoTimers();
  heroInfoAutoShowActive = true;
  heroInfoCard.classList.add('visible');
  heroInfoToggle?.setAttribute('aria-expanded', 'true');
  heroInfoAutoCloseTimer = setTimeout(() => {
    heroInfoAutoShowActive = false;
    heroInfoAutoCloseTimer = null;
    closeHeroInfoCard();
  }, HERO_INFO_AUTO_VISIBLE_MS);
}

if (surveyModal) {
  new MutationObserver(() => {
    if (surveyModal.hidden && !heroInfoSurveyClosed) {
      queueHeroInfoAfterSurveyClose();
    }
  }).observe(surveyModal, { attributes: true, attributeFilter: ['hidden'] });
}

heroInfoToggle?.addEventListener('click', (event) => {
  event.preventDefault();
  if (heroInfoCard?.classList.contains('visible')) closeHeroInfoCard();
  else openHeroInfoCard({ manual: true });
});
heroInfoLink?.addEventListener('click', (event) => {
  event.preventDefault();
  if (heroInfoCurrentMovie?.id) openMovieDetails(heroInfoCurrentMovie.id);
});
document.addEventListener('click', (event) => {
  if (heroInfo && !heroInfo.contains(event.target)) closeHeroInfoCard();
});

function advanceHeroMovie() {
  if (heroMovies.length < 2) return;
  heroIndex = (heroIndex + 1) % heroMovies.length;
  showHeroMovie(heroMovies[heroIndex]);
  preloadHeroImage(heroImageUrl(heroMovies[(heroIndex + 1) % heroMovies.length]));
}

function resumeHeroRotation() {
  if (!uiPreferences.motionEnabled || heroTimer || heroMovies.length < 2) return;
  heroTimer = setInterval(advanceHeroMovie, HERO_ROTATE_MS);
}

function startHeroRotation(movies) {
  stopHeroRotation();
  heroMovies = (movies || []).filter((movie) => heroImageUrl(movie));
  if (!heroMovies.length) return;
  heroIndex = 0;
  showHeroMovie(heroMovies[0]);
  preloadHeroImage(heroImageUrl(heroMovies[1] || heroMovies[0]));
  resumeHeroRotation();
}

function loadSavedSurveyMovie() {
  try {
    const raw = localStorage.getItem(SURVEY_MOVIE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_) {
    return null;
  }
}

function saveSurveyMovie(movie) {
  try { localStorage.setItem(SURVEY_MOVIE_KEY, JSON.stringify(movie)); } catch (_) { /* private mode: skip persisting */ }
}

async function initHeroBackdrop() {
  if (!featuredBackdrop || heroLayerEls.length < 2) return;
  const savedMovie = loadSavedSurveyMovie();
  let trendingMovies = [];
  try {
    const response = await fetch('/api/trending?window=day');
    const data = await response.json();
    if (response.ok) trendingMovies = data.movies || [];
  } catch (_) {
    // Trend filmler alınamadı; anket filmi varsa yine de o gösterilir.
  }
  const queue = [];
  const seenIds = new Set();
  if (savedMovie && heroImageUrl(savedMovie)) {
    queue.push(savedMovie);
    if (savedMovie.id) seenIds.add(savedMovie.id);
  }
  trendingMovies.forEach((movie) => {
    if (!heroImageUrl(movie) || (movie.id && seenIds.has(movie.id))) return;
    if (movie.id) seenIds.add(movie.id);
    queue.push(movie);
  });
  // Anket filmi ilk slide'dır, sonrasında karusel TMDB filmleriyle sürer;
  // hiçbir durumda tek bir filme kilitlenmez (startHeroRotation zaten döngüyü kurar).
  startHeroRotation(queue);
}

function renderMovieCards(movies, requestText) {
  const requestContext = requestText ? `<div class="recommendation-context"><span>İsteğin:</span><strong>${escapeHtml(requestText)}</strong></div>` : '';
  recommendations.innerHTML = requestContext + movies.map((movie) => {
    const overview = String(movie.overview || movie.note || 'Kısa konu bilgisi bulunmuyor.').trim();
    const shortOverview = overview.length > 185 ? `${overview.slice(0, 182).replace(/\s+\S*$/, '')}…` : overview;
    return `<article class="recommendation" data-movie-id="${movie.id}" role="button" tabindex="0" aria-label="${escapeHtml(movie.title)} film detaylarını aç">
      <div class="poster-art"><img src="${movie.poster_url || posterFor(movie)}" alt="${escapeHtml(movie.title)} afişi" />${movieSaveActionsHtml(movie)}</div>
      <div class="recommendation-copy"><h3>${escapeHtml(movie.title)} <span class="meta">${movie.year}</span></h3>
      <small class="movie-genre">${escapeHtml(movie.genres.join(' · '))}</small>${movie.rating ? `<small class="movie-rating">★ ${Number(movie.rating).toFixed(1)}</small>` : ''}
      <p class="recommendation-note">${escapeHtml(shortOverview)}</p><span class="source-badge">${escapeHtml(movie.source || 'TMDB Güncel Katalog')}</span><span class="recommendation-open">Detayları gör →</span></div>
    </article>`;
  }).join('');
  updateFeatured(movies[0]);
}

function revealRecommendationResults() {
  if (!recommendationResults) return;
  recommendationResults.hidden = false;
}

function scrollToRenderedRecommendationResults() {
  if (!recommendationResults || !recommendations?.querySelector('.recommendation')) return;
  // Kartların DOM'a yerleşmesini iki frame boyunca bekle; loading aşamasında
  // kaydırma yapılmaz ve sonuç alanı gerçek yüksekliğiyle ölçülür.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const offset = window.innerWidth <= 640 ? 20 : 36;
      const targetY = recommendationResults.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
    });
  });
}

function providerSection(label, providers) {
  if (!providers?.length) return '';
  return `<section class="provider-group"><h4>${label}</h4><div class="provider-list">${providers.map((provider) => `
    <span class="provider-chip">${provider.logo_url ? `<img src="${escapeHtml(provider.logo_url)}" alt="" />` : ''}${escapeHtml(provider.name)}</span>
  `).join('')}</div></section>`;
}

function closeMovieDetails() {
  movieDetailModal.hidden = true;
  document.body.classList.remove('detail-open');
}

async function openMovieDetails(movieId) {
  movieDetailModal.hidden = false;
  document.body.classList.add('detail-open');
  movieDetailContent.innerHTML = '<div class="movie-detail-loading">Film ayrıntıları TMDB’den getiriliyor…</div>';
  try {
    const response = await fetch(`/api/movie/${movieId}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Film ayrıntıları getirilemedi.');
    const movie = data.movie;
    registerSavedMovie(movie);
    const providers = data.providers;
    const platformSections = [
      providerSection('Abonelikle izle', providers.stream),
      providerSection('Kirala', providers.rent),
      providerSection('Satın al', providers.buy)
    ].join('');
    const platformContent = platformSections || '<p class="provider-empty">Bu film için Türkiye’de platform bilgisi bulunamadı.</p>';
    movieDetailContent.innerHTML = `
      <div class="movie-detail-poster"><img src="${escapeHtml(movie.poster_url || posterFor(movie))}" alt="${escapeHtml(movie.title)} afişi" /></div>
      <div class="movie-detail-copy">
        <p class="movie-detail-label">TMDB FİLM DETAYI</p>
        <h2 id="movie-detail-title">${escapeHtml(movie.title)}</h2>
        <p class="movie-detail-meta">${escapeHtml(movie.year)} · ${escapeHtml(movie.genres.join(' · '))}${movie.runtime ? ` · ${escapeHtml(movie.runtime)} dk` : ''}${movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : ''}</p>
        ${movieSaveActionsHtml(movie, 'movie-detail-save-actions')}
        <p class="movie-detail-overview">${escapeHtml(movie.overview || movie.note || 'Konu bilgisi bulunmuyor.')}</p>
        <dl class="movie-detail-people">
          <div><dt>Yönetmen</dt><dd>${escapeHtml(movie.directors.join(', ') || 'Bilgi bulunmuyor')}</dd></div>
          <div><dt>Oyuncular</dt><dd>${escapeHtml(movie.cast.slice(0, 6).join(', ') || 'Bilgi bulunmuyor')}</dd></div>
          <div><dt>Orijinal adı</dt><dd>${escapeHtml(movie.original_title || movie.title)}</dd></div>
        </dl>
        <section class="watch-area"><h3>Türkiye’de nerede izlenir?</h3>${platformContent}
          <p class="provider-credit">Platform bilgileri JustWatch tarafından sağlanmaktadır.${providers.link ? ` <a href="${escapeHtml(providers.link)}" target="_blank" rel="noopener noreferrer">Güncel seçenekleri aç ↗</a>` : ''}</p>
        </section>
        <section class="movie-detail-blog" data-movie-id="${movie.id}">
          <h3>Seyirciler bu film hakkında ne yazmış?</h3>
          <div class="movie-detail-blog-list"><p class="movie-detail-blog-loading">Yükleniyor…</p></div>
        </section>
      </div>`;
    loadMovieDetailBlogPosts(movie.id);
  } catch (error) {
    movieDetailContent.innerHTML = `<div class="movie-detail-loading">${escapeHtml(error.message)}</div>`;
  }
}

// Modal ana içeriğini bloke etmeden, aynı filme ait Seyirci Yazıları'nı ayrıca getirir.
async function loadMovieDetailBlogPosts(movieId) {
  const selector = `.movie-detail-blog[data-movie-id="${movieId}"] .movie-detail-blog-list`;
  if (!movieDetailContent.querySelector(selector)) return;
  try {
    const response = await fetch(`/api/blog/posts?movie_id=${encodeURIComponent(movieId)}&page=1`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Yazılar getirilemedi.');
    const target = movieDetailContent.querySelector(selector);
    if (!target) return;
    const posts = (data.posts || []).slice(0, 4);
    if (!posts.length) {
      target.innerHTML = '<p class="movie-detail-blog-empty">Bu film hakkında henüz bir seyirci yazısı yok.</p>';
      return;
    }
    target.innerHTML = posts.map((post) => `<a class="movie-detail-blog-item" href="/blog/${post.id}">
      <span class="movie-detail-blog-item-type">${escapeHtml(post.post_type || '')}</span>
      <span class="movie-detail-blog-item-title">${escapeHtml(post.title)}</span>
      <span class="movie-detail-blog-item-meta">${escapeHtml(post.author_name)} · ${escapeHtml(post.date_label || '')}</span>
    </a>`).join('') + `<a class="movie-detail-blog-all" href="/blog?movie_id=${encodeURIComponent(movieId)}">Tümünü gör (${data.total}) →</a>`;
  } catch (error) {
    const target = movieDetailContent.querySelector(selector);
    if (target) target.innerHTML = `<p class="movie-detail-blog-empty">${escapeHtml(error.message)}</p>`;
  }
}

recommendations?.addEventListener('click', (event) => {
  const card = event.target.closest('[data-movie-id]');
  if (card) openMovieDetails(card.dataset.movieId);
});
recommendations?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  const card = event.target.closest('[data-movie-id]');
  if (!card) return;
  event.preventDefault();
  openMovieDetails(card.dataset.movieId);
});

let trendingMoviesCache = [];
let editorialActiveMovieId = null;

function renderTrendingMovies(movies) {
  if (!trendingTrack) return;
  trendingMoviesCache = movies || [];
  if (!movies?.length) {
    trendingTrack.innerHTML = '<p class="trending-error">Bu zaman aralığında trend film bulunamadı.</p>';
    return;
  }
  trendingTrack.innerHTML = movies.map((movie) => {
    const meta = [movie.year, movie.rating ? `★ ${Number(movie.rating).toFixed(1)}` : ''].filter(Boolean).join(' · ');
    return `<article class="trending-card" role="button" tabindex="0" data-movie-id="${movie.id}" aria-label="${escapeHtml(movie.title)} önizlemesini göster">
      <span class="trending-poster"><img src="${escapeHtml(movie.poster_url || posterFor(movie))}" alt="${escapeHtml(movie.title)} afişi" loading="lazy" />${movieSaveActionsHtml(movie)}</span>
      <h3>${escapeHtml(movie.title)}</h3><p>${escapeHtml(meta)}</p>
    </article>`;
  }).join('');
}

function setEditorialFeature(movie) {
  if (!movie || !editorialFeature) return;
  if (editorialActiveMovieId === movie.id) return;
  editorialActiveMovieId = movie.id;
  const overview = String(movie.overview || movie.note || '').trim();
  const shortOverview = overview.length > 220 ? `${overview.slice(0, 217).replace(/\s+\S*$/, '')}…` : overview;
  editorialFeature.dataset.movieId = movie.id;
  editorialFeature.setAttribute('aria-label', `${movie.title} film detaylarını aç`);
  editorialFeature.hidden = false;
  editorialTitle.textContent = movie.title;
  if (editorialMeta) {
    const rating = movie.rating ? `★ ${Number(movie.rating).toFixed(1)}` : '';
    editorialMeta.textContent = [movie.year, (movie.genres || []).join(' · '), rating].filter(Boolean).join(' · ');
  }
  editorialNote.textContent = shortOverview;
  if (editorialSaveActions) editorialSaveActions.innerHTML = movieSaveActionsHtml(movie);
  const url = movie.backdrop_url || movie.poster_url;
  if (editorialBackdrop && url) {
    editorialBackdrop.classList.add('fading');
    const preload = new Image();
    preload.onload = () => {
      editorialBackdrop.style.backgroundImage = `url("${url}")`;
      requestAnimationFrame(() => editorialBackdrop.classList.remove('fading'));
    };
    preload.src = url;
  }
}

async function loadTrending(windowName = 'day') {
  if (!trendingTrack) return;
  trendingButtons.forEach((item) => {
    const selected = item.dataset.trendingWindow === windowName;
    item.classList.toggle('active', selected);
    item.setAttribute('aria-pressed', String(selected));
  });
  trendingTrack.innerHTML = '<p class="trending-loading">Trend filmler getiriliyor…</p>';
  try {
    const response = await fetch(`/api/trending?window=${windowName}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Trend filmler getirilemedi.');
    renderTrendingMovies(data.movies);
    if (data.movies?.length) setEditorialFeature(data.movies[0]);
  } catch (error) {
    trendingTrack.innerHTML = `<p class="trending-error">${escapeHtml(error.message)}</p>`;
  }
}

function trendingMovieFromCard(card) {
  if (!card) return null;
  return trendingMoviesCache.find((movie) => String(movie.id) === card.dataset.movieId) || null;
}

trendingButtons.forEach((item) => item.addEventListener('click', () => loadTrending(item.dataset.trendingWindow)));
// Hover/klavye odağı önizleme panelini günceller; TMDb'ye tekrar istek atmaz,
// zaten çekilmiş trendingMoviesCache verisini kullanır.
trendingTrack?.addEventListener('mouseover', (event) => {
  const movie = trendingMovieFromCard(event.target.closest('.trending-card[data-movie-id]'));
  if (movie) setEditorialFeature(movie);
});
trendingTrack?.addEventListener('focusin', (event) => {
  const movie = trendingMovieFromCard(event.target.closest('.trending-card[data-movie-id]'));
  if (movie) setEditorialFeature(movie);
});
// Touch/klik: karta basınca hem önizleme banner'ı güncellenir hem de
// film hakkında bilgi doğrudan açılır.
trendingSection?.addEventListener('click', (event) => {
  const movie = trendingMovieFromCard(event.target.closest('.trending-card[data-movie-id]'));
  if (!movie) return;
  setEditorialFeature(movie);
  openMovieDetails(movie.id);
});
trendingSection?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  const movie = trendingMovieFromCard(event.target.closest('.trending-card[data-movie-id]'));
  if (!movie) return;
  event.preventDefault();
  setEditorialFeature(movie);
  openMovieDetails(movie.id);
});
editorialFeature?.addEventListener('click', () => openMovieDetails(editorialFeature.dataset.movieId));
editorialFeature?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  event.preventDefault();
  openMovieDetails(editorialFeature.dataset.movieId);
});
movieDetailClose?.addEventListener('click', closeMovieDetails);
movieDetailModal?.addEventListener('click', (event) => {
  if (event.target === movieDetailModal) closeMovieDetails();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && trailerModal && !trailerModal.hidden) closeTrailerModal();
  else if (event.key === 'Escape' && movieDetailModal && !movieDetailModal.hidden) closeMovieDetails();
  else if (event.key === 'Escape' && document.body.classList.contains('nav-open')) setNavigationCollapsed(true);
});

function chatSourceHtml(movie) {
  const score = movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : '';
  return `<div class="chat-source">${movie.poster_url ? `<img src="${escapeHtml(movie.poster_url)}" alt="" loading="lazy" />` : '<span></span>'}<div><strong>${escapeHtml(movie.title)}</strong><small>${escapeHtml(movie.year)}${score}</small></div></div>`;
}

function chatMessageHtml(message) {
  const isUser = message.role === 'user';
  const film = !isUser && message.movieTitle ? `<div class="chat-film-context">${escapeHtml(message.movieTitle)}${message.movieYear ? `<small>${escapeHtml(message.movieYear)}</small>` : ''}</div>` : '';
  const sources = !isUser && message.matches?.length ? `<details class="chat-message-sources"><summary>Bu yanıtta kullanılan film kaydı</summary><div class="chat-source-list">${message.matches.map(chatSourceHtml).join('')}</div></details>` : '';
  return `<article class="chat-message ${isUser ? 'user' : 'assistant'}"><div class="chat-bubble"><span class="chat-speaker">${isUser ? 'SEN' : 'FİLM SOHBETİ'}</span>${film}<p>${escapeHtml(message.content)}</p>${sources}</div></article>`;
}

function renderChatConversation() {
  if (!chatHistory) return;
  const messages = chatMessages.length ? chatMessages : [{
    role: 'assistant',
    content: 'TMDb Top 250\'den bir film seç veya adını yaz. Karakterleri, yönetmeni, hikâyeyi ya da film hakkındaki düşüncelerini konuşabiliriz.',
  }];
  chatHistory.innerHTML = messages.map(chatMessageHtml).join('') + (chatIsLoading ? '<article class="chat-message assistant"><div class="chat-bubble"><span class="chat-speaker">FİLM SOHBETİ</span><span class="chat-typing" aria-label="Yanıt hazırlanıyor"><i></i><i></i><i></i></span></div></article>' : '');
  requestAnimationFrame(() => { chatHistory.scrollTop = chatHistory.scrollHeight; });
}

function updateSelectedMovieIndicator(movie) {
  if (movie) activeChatMovieMeta = { title: movie.title, year: movie.year, directors: movie.directors || [] };
  if (!chatSelectedMovie) return;
  if (!activeChatMovieId || !activeChatMovieMeta) {
    chatSelectedMovie.hidden = true;
    if (chatFilmPicker) chatFilmPicker.hidden = false;
    return;
  }
  if (chatSelectedTitle) chatSelectedTitle.textContent = activeChatMovieMeta.title || '';
  if (chatSelectedMeta) {
    chatSelectedMeta.textContent = [activeChatMovieMeta.year, activeChatMovieMeta.directors?.[0]].filter(Boolean).join(' · ');
  }
  chatSelectedMovie.hidden = false;
  if (chatFilmPicker) chatFilmPicker.hidden = true;
}

function setSpoilerMode(enabled) {
  spoilerMode = enabled;
  chatSpoilerOff?.classList.toggle('active', !enabled);
  chatSpoilerOff?.setAttribute('aria-pressed', String(!enabled));
  chatSpoilerOn?.classList.toggle('active', enabled);
  chatSpoilerOn?.setAttribute('aria-pressed', String(enabled));
}

function saveChatConversation() {
  if (!chatHistory) return;
  try {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify({
      messages: chatMessages.slice(-40), movieId: activeChatMovieId, movieMeta: activeChatMovieMeta, spoiler: spoilerMode,
    }));
  } catch (_) { /* Sohbet saklanamasa da canlı konuşma çalışmaya devam eder. */ }
}

function restoreChatConversation() {
  if (!chatHistory) return;
  try {
    const saved = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) || '{}');
    chatMessages = Array.isArray(saved.messages) ? saved.messages.slice(-40) : [];
    activeChatMovieId = Number(saved.movieId) || null;
    activeChatMovieMeta = saved.movieMeta || null;
    setSpoilerMode(Boolean(saved.spoiler));
  } catch (_) {
    chatMessages = [];
    activeChatMovieId = null;
    activeChatMovieMeta = null;
  }
  updateSelectedMovieIndicator();
  renderChatConversation();
}

function resetChatFilm() {
  chatMessages = [];
  activeChatMovieId = null;
  activeChatMovieMeta = null;
  localStorage.removeItem(CHAT_STORAGE_KEY);
  updateSelectedMovieIndicator();
  renderChatConversation();
  if (chatFilmSearch) chatFilmSearch.value = '';
  if (chatFilmResults) chatFilmResults.hidden = true;
  query?.focus();
}

chatClear?.addEventListener('click', resetChatFilm);
chatChangeMovie?.addEventListener('click', resetChatFilm);

chatSpoilerOff?.addEventListener('click', () => { setSpoilerMode(false); saveChatConversation(); });
chatSpoilerOn?.addEventListener('click', () => { setSpoilerMode(true); saveChatConversation(); });

function renderChatFilmResults(movies) {
  if (!chatFilmResults) return;
  if (!movies.length) {
    chatFilmResults.innerHTML = '<p class="chat-film-empty">Top 250 içinde eşleşen film yok.</p>';
    chatFilmResults.hidden = false;
    return;
  }
  chatFilmResults.innerHTML = movies.map((movie) => `<button class="chat-film-result" type="button" data-movie-id="${movie.id}" data-title="${escapeHtml(movie.title)}" data-year="${escapeHtml(String(movie.year))}" data-director="${escapeHtml(movie.directors?.[0] || '')}">${escapeHtml(movie.title)} <small>${escapeHtml(String(movie.year))}</small></button>`).join('');
  chatFilmResults.hidden = false;
}

chatFilmSearch?.addEventListener('input', (event) => {
  const value = event.target.value.trim();
  clearTimeout(chatFilmSearchTimer);
  if (value.length < 2) {
    if (chatFilmResults) chatFilmResults.hidden = true;
    return;
  }
  chatFilmSearchTimer = setTimeout(async () => {
    try {
      const response = await fetch(`/api/chat/top250-search?q=${encodeURIComponent(value)}`);
      const data = await response.json();
      renderChatFilmResults(data.movies || []);
    } catch (_) {
      if (chatFilmResults) chatFilmResults.hidden = true;
    }
  }, 300);
});

chatFilmResults?.addEventListener('click', (event) => {
  const item = event.target.closest('.chat-film-result[data-movie-id]');
  if (!item) return;
  chatMessages = [];
  activeChatMovieId = Number(item.dataset.movieId);
  activeChatMovieMeta = { title: item.dataset.title, year: item.dataset.year, directors: item.dataset.director ? [item.dataset.director] : [] };
  chatMessages.push({
    role: 'assistant',
    content: activeChatMovieMeta.directors[0]
      ? `${activeChatMovieMeta.directors[0]} · ${activeChatMovieMeta.year}\n\nBu film hakkında düşündüklerini paylaşabilir, karakterleri veya yönetmeni konuşabiliriz.`
      : 'Bu film hakkında düşündüklerini paylaşabilir, karakterleri veya yönetmeni konuşabiliriz.',
    movieTitle: activeChatMovieMeta.title, movieYear: activeChatMovieMeta.year,
  });
  chatFilmResults.hidden = true;
  chatFilmSearch.value = '';
  updateSelectedMovieIndicator();
  saveChatConversation();
  renderChatConversation();
  query?.focus();
});

document.addEventListener('click', (event) => {
  if (chatFilmPicker && !chatFilmPicker.contains(event.target)) { if (chatFilmResults) chatFilmResults.hidden = true; }
});

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const value = query.value.trim();
  if (value.length < 2 || chatIsLoading) return;
  const priorHistory = chatMessages.slice(-6).map((item) => ({ role: item.role, content: item.content }));
  query.value = '';
  chatMessages.push({ role: 'user', content: value });
  chatIsLoading = true;
  button.disabled = true;
  button.querySelector('span').textContent = '…';
  renderChatConversation();
  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: value, source: selectedSource, movieId: activeChatMovieId, history: priorHistory, spoiler: spoilerMode })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Sohbet yanıtı hazırlanamadı.');
    const leadMovie = data.leadMovie || data.matches?.[0];
    activeChatMovieId = leadMovie?.id || activeChatMovieId;
    if (leadMovie) updateSelectedMovieIndicator(leadMovie);
    chatMessages.push({
      role: 'assistant', content: data.answer, movieTitle: leadMovie?.title || '', movieYear: leadMovie?.year || '',
      matches: (data.matches || []).slice(0, 3).map((movie) => ({ id: movie.id, title: movie.title, year: movie.year, rating: movie.rating, poster_url: movie.poster_url }))
    });
  } catch (error) {
    chatMessages.push({ role: 'assistant', content: error.message });
  } finally {
    chatIsLoading = false;
    button.disabled = false;
    button.querySelector('span').textContent = '→';
    saveChatConversation();
    renderChatConversation();
    query.focus();
  }
});

function escapeHtml(value) {
  const element = document.createElement('span');
  element.textContent = value;
  return element.innerHTML;
}

quizButton?.addEventListener('click', startQuiz);
nextQuestion?.addEventListener('click', loadQuiz);
finishQuiz?.addEventListener('click', finishQuizGame);
quizSummary?.addEventListener('click', (event) => {
  if (event.target.closest('[data-restart-quiz]')) startQuiz();
});

function startQuiz() {
  quizStats = { correct: 0, incorrect: 0, total: 0, combo: 0, bestCombo: 0, xp: 0 };
  // Her yeni oyun bağımsız bir turdur; önceki turun XP ve rozetleri taşınmaz.
  quizProgress = { xp: 0, total: 0, correct: 0, posterCorrect: 0, bestCombo: 0, sessions: 0, badges: [] };
  saveQuizProgress();
  quizSummary.hidden = true;
  quizSummary.classList.remove('quiz-summary-visible');
  renderQuizRewards();
  loadQuiz();
}

async function loadQuiz() {
  quiz.hidden = false;
  quizCard.classList.add('is-playing');
  quizButton.hidden = true;
  quizButton.disabled = true;
  if (quizRewardBar) quizRewardBar.hidden = false;
  if (quizTopline) quizTopline.hidden = false;
  if (quizQuestionRow) quizQuestionRow.hidden = false;
  quizSummary.hidden = true;
  quizSummary.classList.remove('quiz-summary-visible');
  quizQuestion.hidden = false;
  quizChoices.hidden = false;
  finishQuiz.hidden = false;
  quizPoster.hidden = true;
  quizQuestion.textContent = 'Soru hazırlanıyor…';
  quizChoices.innerHTML = '';
  quizFeedback.hidden = true;
  nextQuestion.hidden = true;
  try {
    const response = await fetch('/api/quiz');
    if (!response.ok) throw new Error('Soru yüklenemedi.');
    currentQuiz = await response.json();
    currentQuiz.answered = false;
    quizCategory.textContent = currentQuiz.category.toUpperCase();
    quizQuestion.textContent = currentQuiz.question;
    if (currentQuiz.questionType === 'poster' && currentQuiz.posterUrl) {
      quizPosterImage.src = currentQuiz.posterUrl;
      quizPosterImage.alt = currentQuiz.movieTitle ? `${currentQuiz.movieTitle} afişi` : 'Film afişi';
      quizPoster.hidden = false;
    }
    currentQuiz.displayChoices.forEach((displayChoice, index) => {
      const choice = currentQuiz.choices[index];
      const choiceButton = document.createElement('button');
      choiceButton.type = 'button';
      choiceButton.className = 'quiz-choice';
      choiceButton.dataset.value = choice;
      choiceButton.innerHTML = `<span class="letter">${String.fromCharCode(65 + index)}</span><span>${escapeHtml(displayChoice)}</span>`;
      choiceButton.addEventListener('click', () => checkQuiz(choice, choiceButton));
      quizChoices.appendChild(choiceButton);
    });
  } catch (error) {
    quizQuestion.textContent = error.message;
  } finally {
    quizButton.disabled = false;
  }
}

async function checkQuiz(choice, selectedButton) {
  if (currentQuiz.answered) return;
  currentQuiz.answered = true;
  const buttons = [...quizChoices.querySelectorAll('button')];
  selectedButton.classList.add('selected');
  buttons.forEach((button) => { button.disabled = true; });
  try {
    const response = await fetch('/api/quiz/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentQuiz.id, choice })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Cevap kontrol edilemedi.');
    const reward = recordQuizReward(data.correct, data.questionType || currentQuiz.questionType);
    const correctButton = buttons.find((button) => button.dataset.value === data.answer);
    if (correctButton) correctButton.classList.add('correct');
    if (!data.correct) selectedButton.classList.add('incorrect');
    const awardCopy = reward.unlocked.length
      ? `<div class="quiz-award"><b>Yeni rozet:</b> ${reward.unlocked.map((badge) => `${badge.icon} ${badge.name}`).join(' · ')}</div>`
      : '';
    quizFeedback.innerHTML = data.correct
      ? `<strong>Doğru cevap.</strong> +${reward.earnedXp} XP kazandın.${awardCopy}`
      : `Doğru cevap: <strong>${escapeHtml(data.answerDisplay)}</strong>${awardCopy}`;
    quizFeedback.hidden = false;
    nextQuestion.hidden = false;
  } catch (error) {
    currentQuiz.answered = false;
    buttons.forEach((button) => { button.disabled = false; });
    quizFeedback.textContent = error.message;
    quizFeedback.hidden = false;
  }
}

function quizTitleFor(score, total) {
  if (!total) return ['Isınma Turu', 'Bir soru seçmeden oyunu bitirdin. Yeni turda perdeyi açalım.'];
  if (score >= 90) return ['Film Gurmesi', 'Mükemmel bir tur. Bu sinema bilgisi jenerikte tek başına akar.'];
  if (score >= 70) return ['Perde Dedektifi', 'Detayları kaçırmıyorsun; birkaç tur daha ve ustalık sende.'];
  if (score >= 45) return ['Sahne Avcısı', 'Güçlü bir başlangıç. Bir sonraki turda daha çok ipucu yakalarsın.'];
  return ['Cesur Seyirci', 'Her büyük film küçük bir ilk sahneyle başlar. Bir tur daha dene.'];
}

function finishQuizGame() {
  const buttons = [...quizChoices.querySelectorAll('button')];
  buttons.forEach((item) => { item.disabled = true; });
  const score = quizStats.total ? Math.round((quizStats.correct / quizStats.total) * 100) : 0;
  const [title, copy] = quizTitleFor(score, quizStats.total);
  if (quizStats.total) {
    quizProgress.sessions += 1;
    saveQuizProgress();
  }
  // Oyun bitince playing state'e ait hiçbir şey (reward bar, başlık, soru,
  // seçenekler, geri bildirim) DOM'da görünür kalmaz — yalnızca sonuç kartı render edilir.
  if (quizRewardBar) quizRewardBar.hidden = true;
  if (quizTopline) quizTopline.hidden = true;
  if (quizQuestionRow) quizQuestionRow.hidden = true;
  quizPoster.hidden = true;
  quizQuestion.hidden = true;
  quizChoices.hidden = true;
  quizFeedback.hidden = true;
  nextQuestion.hidden = true;
  finishQuiz.hidden = true;
  const unlockedBadges = QUIZ_BADGES.filter((badge) => quizProgress.badges.includes(badge.id));
  const badgeMarkup = unlockedBadges.length
    ? `<div class="quiz-badges">${unlockedBadges.map((badge) => `<span class="quiz-badge"><span>${badge.icon}</span>${badge.name}</span>`).join('')}</div>`
    : '';
  quizSummary.innerHTML = `<p class="quiz-summary-label">OYUN TAMAMLANDI</p>
    <h3>${title}</h3><p class="quiz-summary-copy">${copy}</p>
    <div class="quiz-result-card">
      <div class="quiz-scoreboard"><div class="score-ring" style="--score-angle:${score * 3.6}deg"><strong>%${score}</strong><span>DOĞRULUK</span></div>
        <div class="score-counts"><div class="score-count correct"><b>✓ ${quizStats.correct}</b><span>DOĞRU</span></div><div class="score-count incorrect"><b>× ${quizStats.incorrect}</b><span>YANLIŞ</span></div></div></div>
      <div class="quiz-xp-row"><div class="quiz-xp-stat"><span>BU TUR</span><b>+${quizStats.xp} XP</b></div><div class="quiz-xp-divider"></div><div class="quiz-xp-stat"><span>TOPLAM</span><b>${quizProgress.xp} XP</b></div></div>
      ${badgeMarkup}
    </div>
    <button class="quiz-restart" type="button" data-restart-quiz>Yeni oyun başlat →</button>`;
  quizSummary.hidden = false;
  requestAnimationFrame(() => quizSummary.classList.add('quiz-summary-visible'));
}

renderQuizRewards();

moodForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mood = moodInput.value.trim();
  if (mood.length < 2) return;
  recommendations.textContent = 'Sana uygun filmler aranıyor…';
  revealRecommendationResults();
  try {
    const response = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood, source: selectedSource })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Öneriler getirilemedi.');
    renderMovieCards(data.recommendations, mood);
    scrollToRenderedRecommendationResults();
  } catch (error) {
    recommendations.textContent = error.message;
  }
});

const surveySteps = [
  { key: 'mood', question: 'Bu akşam nasıl hissediyorsun?', options: ['Yorgun ve sakin', 'Keyifsiz veya duygusal', 'Enerjik ve hareketli'] },
  { key: 'filmStyle', question: 'Nasıl bir film istiyorsun?', options: ['Komik ve hafif', 'Gizemli ve düşündürücü', 'Romantik ve sıcak'] },
  { key: 'pace', question: 'Tempo tercihin nedir?', options: ['Yavaş ve rahat', 'Akıcı ve meraklı', 'Hızlı ve heyecanlı'] },
  { key: 'feeling', question: 'Bu akşam ne hissetmek istiyorsun?', options: ['Gülümsemek', 'Düşünmek', 'Başka bir dünyaya kaçmak'] }
];
let surveyStep = 0;
const surveyState = { age: '', gender: '', mood: '', filmStyle: '', pace: '', feeling: '' };

function renderSurvey() {
  surveyBox.classList.remove('survey-result-mode');
  surveyResult.hidden = true;
  surveyProgress.hidden = false;
  const surveyProgressValue = ((surveyStep + 1) / 5) * 100;
  surveyProgress.setAttribute('aria-valuenow', String(surveyProgressValue));
  surveyBox.style.setProperty('--survey-progress', `${surveyProgressValue}%`);
  if (surveyStep === 0) {
    surveyTitle.hidden = false;
    surveyQuestion.hidden = true;
    surveyQuestion.classList.remove('survey-question-main');
    surveyDemographics.hidden = false;
    surveyOptions.hidden = true;
    return;
  }
  const step = surveySteps[surveyStep - 1];
  surveyTitle.hidden = true;
  surveyQuestion.hidden = false;
  surveyQuestion.classList.add('survey-question-main');
  surveyQuestion.textContent = step.question;
  surveyDemographics.hidden = true;
  surveyOptions.hidden = false;
  surveyOptions.replaceChildren();
  step.options.forEach((option) => {
    const optionButton = document.createElement('button');
    optionButton.className = 'survey-option';
    optionButton.type = 'button';
    optionButton.textContent = option;
    optionButton.addEventListener('click', () => answerSurvey(step.key, option));
    surveyOptions.appendChild(optionButton);
  });
}

function selectGender(gender) {
  surveyState.gender = gender;
  genderOptions.querySelectorAll('button').forEach((item) => item.classList.toggle('selected', item.dataset.gender === gender));
  demographicsNext.disabled = !surveyAge.validity.valid || !surveyAge.value;
}

genderOptions?.querySelectorAll('button').forEach((item) => item.addEventListener('click', () => selectGender(item.dataset.gender)));
surveyAge?.addEventListener('input', () => { demographicsNext.disabled = !surveyAge.validity.valid || !surveyAge.value; });
demographicsNext?.addEventListener('click', () => {
  if (!surveyAge.validity.valid || !surveyAge.value) return;
  surveyState.age = surveyAge.value;
  surveyState.gender ||= 'Belirtmek istemiyorum';
  surveyStep = 1;
  renderSurvey();
});

async function answerSurvey(key, choice) {
  surveyState[key] = choice;
  surveyStep += 1;
  if (surveyStep <= surveySteps.length) {
    renderSurvey();
    return;
  }
  showSurveyLoading();
  const answers = [`Yaş: ${surveyState.age}`, `Cinsiyet: ${surveyState.gender}`, surveyState.mood, surveyState.filmStyle, surveyState.pace, surveyState.feeling];
  try {
    const response = await fetch('/api/survey-recommend', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ answers, profile: surveyState })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Öneri hazırlanamadı.');
    const movie = data.movie;
    saveSurveyMovie(movie);
    const poster = movie.poster_url || posterFor(movie);
    const rating = movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : '';
    updateFeatured(movie);
    renderSurveyResult(movie, poster, rating);
  } catch (error) {
    surveyResult.innerHTML = '<p class="survey-result-label">BUGÜNE ÖZEL</p><p class="survey-result-reason">' + escapeHtml(error.message) + '</p><div class="survey-result-actions"><button class="secondary" type="button" data-survey-action="home">Ana sayfaya geç →</button></div>';
  }
}

function showSurveyLoading() {
  surveyBox.classList.add('survey-result-mode');
  surveyProgress.hidden = true;
  surveyTitle.hidden = true;
  surveyQuestion.hidden = true;
  surveyDemographics.hidden = true;
  surveyOptions.hidden = true;
  surveyResult.hidden = false;
  surveyResult.innerHTML = '<p class="survey-result-label">BUGÜNE ÖZEL</p><div class="survey-result-loading">Sana uygun film seçiliyor…</div>';
}

function renderSurveyResult(movie, poster, rating) {
  const reason = `Bu akşam ${surveyState.mood.toLowerCase()} hissettiğini ve ${surveyState.filmStyle.toLowerCase()} bir hikâye aradığını söyledin. ${movie.title}, seçtiğin tempoya eşlik edecek sıcak bir seçim.`;
  surveyResult.innerHTML = '<p class="survey-result-label">BUGÜNE ÖZEL</p><div class="survey-result-grid"><div class="survey-result-poster"><img src="' + poster + '" alt="' + escapeHtml(movie.title) + ' afişi" />' + movieSaveActionsHtml(movie) + '</div><div><h2>' + escapeHtml(movie.title) + '</h2><p class="survey-result-meta">' + escapeHtml(movie.year) + ' · ' + escapeHtml(movie.genres.join(' · ')) + rating + '</p><span class="source-badge">' + escapeHtml(movie.source || 'TMDB Güncel Katalog') + '</span><p class="survey-result-reason">' + escapeHtml(reason) + '</p><div class="survey-result-actions"><button type="button" data-survey-action="discover" data-movie-id="' + movie.id + '">Filmi keşfet</button><button class="secondary" type="button" data-survey-action="home">Ana sayfaya geç →</button></div></div></div>';
}

surveyResult?.addEventListener('click', (event) => {
  const target = event.target.closest('[data-survey-action]');
  const action = target?.dataset.surveyAction;
  if (!action) return;
  surveyModal.hidden = true;
  queueHeroInfoAfterSurveyClose();
  if (action === 'discover' && target.dataset.movieId) openMovieDetails(target.dataset.movieId);
  if (action === 'home') window.scrollTo({ top: 0, behavior: 'smooth' });
});

if (surveyModal) renderSurvey();
if (trendingSection) loadTrending('day');
if (chatHistory) restoreChatConversation();
initHeroBackdrop();

function savedMovieCardHtml(movie) {
  registerSavedMovie(movie);
  const rating = movie.rating ? `★ ${Number(movie.rating).toFixed(1)}` : '';
  const meta = [movie.year, rating].filter(Boolean).join('   •   ');
  return `<article class="catalog-card saved-movie-card" role="button" tabindex="0" data-movie-id="${movie.id}" aria-label="${escapeHtml(movie.title)} ayrıntılarını aç">
    <span class="catalog-card-poster"><img src="${escapeHtml(movie.poster_url || posterFor(movie))}" alt="${escapeHtml(movie.title)} afişi" loading="lazy" />${movieSaveActionsHtml(movie)}</span>
    <span class="catalog-card-title">${escapeHtml(movie.title)}</span>
    <span class="catalog-card-meta">${escapeHtml(meta)}</span>
  </article>`;
}

function renderSavedMoviesPage() {
  const page = document.querySelector('#saved-movies-page');
  const grid = document.querySelector('#saved-movies-grid');
  const count = document.querySelector('#saved-movies-count');
  if (!page || !grid) return;
  const list = page.dataset.savedList;
  const movies = Object.values(savedMoviesState[list] || {});
  movies.forEach(registerSavedMovie);
  if (count) count.textContent = `${movies.length} film`;
  if (!movies.length) {
    const title = list === 'favorites' ? 'Henüz favori filmin yok.' : 'İzleme listen henüz boş.';
    const sub = list === 'favorites'
      ? 'Beğendiğin filmleri favorilerine eklediğinde burada görebilirsin.'
      : 'Daha sonra izlemek istediğin filmleri buraya ekleyebilirsin.';
    grid.innerHTML = `<div class="saved-movies-empty"><p class="saved-movies-empty-title">${title}</p><p class="saved-movies-empty-sub">${sub}</p><a href="/film-ara">Filmler arasında gezin →</a></div>`;
    return;
  }
  grid.innerHTML = movies.map(savedMovieCardHtml).join('');
  syncSavedMovieControls();
}

const savedMoviesGrid = document.querySelector('#saved-movies-grid');
savedMoviesGrid?.addEventListener('click', (event) => {
  const card = event.target.closest('.saved-movie-card[data-movie-id]');
  if (card) openMovieDetails(card.dataset.movieId);
});
savedMoviesGrid?.addEventListener('keydown', (event) => {
  if (!['Enter', ' '].includes(event.key)) return;
  const card = event.target.closest('.saved-movie-card[data-movie-id]');
  if (!card) return;
  event.preventDefault();
  openMovieDetails(card.dataset.movieId);
});
if (document.body.dataset.authenticated !== 'true') renderSavedMoviesPage();

async function loadAccountMovies() {
  await authReady;
  if (!authState.isAuthenticated) return;
  try {
    const response = await authFetch('/api/user/movies');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Kişisel listeler yüklenemedi.');
    savedMoviesState = emptySavedMoviesState();
    ['favorites', 'watchlist'].forEach((list) => {
      (data[list] || []).forEach((movie) => {
        const normalized = normalizeSavedMovie(movie);
        savedMoviesState[list][String(normalized.id)] = normalized;
        registerSavedMovie(normalized);
      });
    });
    syncSavedMovieControls();
    renderSavedMoviesPage();
  } catch (error) {
    showSavedMovieToast(error.message);
  }
}

loadAccountMovies();

const authForm = document.querySelector('#auth-form');
authForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const submit = authForm.querySelector('.auth-submit');
  const errorBox = document.querySelector('#auth-error');
  const values = Object.fromEntries(new FormData(authForm).entries());
  errorBox.textContent = '';
  submit.disabled = true;
  try {
    const endpoint = authForm.dataset.authMode === 'register' ? '/api/auth/register' : '/api/auth/login';
    const response = await fetch(endpoint, {
      method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'İşlem tamamlanamadı.');
    authState.user = data.user;
    authState.isAuthenticated = true;
    authState.csrfToken = data.csrfToken;
    window.location.assign(authForm.dataset.authNext || '/');
  } catch (error) {
    errorBox.textContent = error.message;
    submit.disabled = false;
  }
});

// Kayıt formunda anlık kullanılabilirlik kontrolü — yalnızca UX içindir,
// asıl doğrulama backend'de (/api/auth/register) yapılır.
if (authForm?.dataset.authMode === 'register') {
  function wireAuthAvailabilityCheck(field) {
    const input = authForm.querySelector(`input[name="${field}"]`);
    const hint = authForm.querySelector(`[data-hint-for="${field}"]`);
    if (!input || !hint) return;
    let timer = null;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const value = input.value.trim();
      input.classList.remove('is-available', 'is-taken');
      if (!value) { hint.textContent = ''; hint.className = 'auth-field-hint'; return; }
      hint.textContent = 'Kontrol ediliyor…';
      hint.className = 'auth-field-hint is-checking';
      timer = setTimeout(async () => {
        try {
          const response = await fetch(`/api/auth/availability?field=${field}&value=${encodeURIComponent(value)}`);
          const data = await response.json();
          if (input.value.trim() !== value) return;
          hint.textContent = data.available ? `✓ ${data.message}` : data.message;
          hint.className = `auth-field-hint ${data.available ? 'is-available' : 'is-taken'}`;
          input.classList.toggle('is-available', data.available);
          input.classList.toggle('is-taken', !data.available);
        } catch (_) {
          hint.textContent = '';
          hint.className = 'auth-field-hint';
        }
      }, 450);
    });
  }
  wireAuthAvailabilityCheck('username');
  wireAuthAvailabilityCheck('email');
}

async function logoutAccount() {
  try {
    const response = await authFetch('/api/auth/logout', { method: 'POST' });
    if (!response.ok) throw new Error('Çıkış yapılamadı.');
    authState.user = null;
    authState.isAuthenticated = false;
    authState.csrfToken = null;
    savedMoviesState = emptySavedMoviesState();
    window.location.assign('/');
  } catch (error) {
    showSavedMovieToast(error.message);
  }
}

document.querySelector('#side-logout')?.addEventListener('click', logoutAccount);
document.querySelector('#profile-logout')?.addEventListener('click', logoutAccount);

// ===== Ayarlar: mevcut localStorage durumlarının tek kontrol yüzeyi =====
const settingsPage = document.querySelector('#settings-page');
if (settingsPage) {
  const spoilerWarningsToggle = document.querySelector('#settings-spoiler-warnings');
  const motionToggle = document.querySelector('#settings-motion');
  const settingsFeedback = document.querySelector('#settings-feedback');

  function setSettingsFeedback(message) {
    settingsFeedback.textContent = message;
  }

  function updateSettingsToggle(toggle) {
    const state = toggle.closest('.settings-toggle')?.querySelector('.settings-toggle-state');
    if (state) state.textContent = toggle.checked ? 'Açık' : 'Kapalı';
  }

  function loadSpoilerWarningsPreference() {
    try {
      const savedChat = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) || '{}');
      return !Boolean(savedChat.spoiler);
    } catch (_) {
      return true;
    }
  }

  spoilerWarningsToggle.checked = loadSpoilerWarningsPreference();
  motionToggle.checked = uiPreferences.motionEnabled;
  updateSettingsToggle(spoilerWarningsToggle);
  updateSettingsToggle(motionToggle);

  spoilerWarningsToggle.addEventListener('change', () => {
    let savedChat = {};
    try { savedChat = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) || '{}'); } catch (_) { savedChat = {}; }
    savedChat.spoiler = !spoilerWarningsToggle.checked;
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(savedChat));
    updateSettingsToggle(spoilerWarningsToggle);
    setSettingsFeedback(spoilerWarningsToggle.checked ? 'Spoiler uyarıları açıldı.' : 'Spoiler uyarıları kapatıldı.');
  });

  motionToggle.addEventListener('change', () => {
    uiPreferences = { ...uiPreferences, motionEnabled: motionToggle.checked };
    localStorage.setItem(UI_PREFERENCES_KEY, JSON.stringify(uiPreferences));
    applyUiPreferences();
    updateSettingsToggle(motionToggle);
    setSettingsFeedback(motionToggle.checked ? 'Hareketli efektler açıldı.' : 'Hareketli efektler azaltıldı.');
  });

  settingsPage.addEventListener('click', async (event) => {
    const action = event.target.closest('[data-settings-clear]')?.dataset.settingsClear;
    if (!action) return;
    const confirmations = {
      favorites: 'Favorilerindeki tüm filmleri kaldırmak istediğine emin misin?',
      watchlist: 'İzleme listesindeki tüm filmleri kaldırmak istediğine emin misin?',
      preferences: 'Film tercihlerini sıfırlamak istediğine emin misin?',
    };
    if (!window.confirm(confirmations[action])) return;

    if (action === 'preferences') {
      localStorage.removeItem(SURVEY_MOVIE_KEY);
      setSettingsFeedback('Film tercihlerin sıfırlandı. Yeniden düzenlemek için anketi açabilirsin.');
      return;
    }
    await authReady;
    if (authState.isAuthenticated) {
      try {
        const response = await authFetch(`/api/user/movies/${action}`, { method: 'DELETE' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Liste temizlenemedi.');
      } catch (error) {
        setSettingsFeedback(error.message);
        return;
      }
    } else {
      const guestMovies = loadSavedMovies();
      guestMovies[action] = {};
      localStorage.setItem(SAVED_MOVIES_KEY, JSON.stringify(guestMovies));
    }
    savedMoviesState[action] = {};
    syncSavedMovieControls();
    renderSavedMoviesPage();
    setSettingsFeedback(action === 'favorites' ? 'Favorilerin temizlendi.' : 'İzleme listen temizlendi.');
  });
}

// ===== Film Ara: canlı TMDB kataloğu + arama + gelişmiş filtreler =====
const catalogGrid = document.querySelector('#catalog-grid');
if (catalogGrid) {
  const catalogSearchForm = document.querySelector('#catalog-search');
  const catalogSearchInput = document.querySelector('#catalog-search-input');
  const catalogGenreList = document.querySelector('#catalog-genre-list');
  const catalogYearFrom = document.querySelector('#catalog-year-from');
  const catalogYearTo = document.querySelector('#catalog-year-to');
  const catalogRatingList = document.querySelector('#catalog-rating-list');
  const catalogRuntimeList = document.querySelector('#catalog-runtime-list');
  const catalogProviderList = document.querySelector('#catalog-provider-list');
  const catalogLanguage = document.querySelector('#catalog-language');
  const catalogSort = document.querySelector('#catalog-sort');
  const catalogChips = document.querySelector('#catalog-chips');
  const catalogCount = document.querySelector('#catalog-count');
  const catalogPagination = document.querySelector('#catalog-pagination');
  const catalogFiltersClear = document.querySelector('#catalog-filters-clear');
  const catalogFilters = document.querySelector('#catalog-filters');
  const catalogFiltersToggle = document.querySelector('#catalog-filters-toggle');
  const catalogFiltersClose = document.querySelector('#catalog-filters-close');
  const catalogFiltersBackdrop = document.querySelector('#catalog-filters-backdrop');
  const catalogGenreToggle = document.querySelector('[data-toggle-for="catalog-genre-list"]');
  const catalogProviderToggle = document.querySelector('[data-toggle-for="catalog-provider-list"]');

  const CATALOG_RUNTIME_LABELS = { short: '90 dk altından kısa', medium: '90–120 dk', long: '120 dk üstü' };

  let catalogCurrentPage = 1;
  let catalogTotalPages = 1;
  let catalogRequestToken = 0;
  let catalogSearchTimer = null;
  const catalogProviderNames = new Map();
  const CATALOG_FEATURED_PROVIDER_COUNT = 8;

  // TÜR ve İZLEME PLATFORMU listeleri uzun olduğu için ilk açılışta yalnızca
  // öne çıkanları gösterir; ".catalog-option-extra" işaretli satırlar
  // "+N daha" ile açılıp kapanır. Seçili bir satır asla tamamen gizlenmez.
  function setupCatalogCollapsibleGroup(container, toggle, moreLabel) {
    if (!container || !toggle) return { refresh() {} };
    let expanded = false;
    function refresh() {
      const extras = [...container.querySelectorAll('.catalog-option-extra')];
      if (!extras.length) { toggle.hidden = true; return; }
      const entering = [];
      extras.forEach((item) => {
        const input = item.querySelector('input');
        const shouldShow = expanded || Boolean(input?.checked);
        if (shouldShow && item.hidden) entering.push(item);
        item.hidden = !shouldShow;
      });
      entering.forEach((item) => item.classList.add('catalog-option-enter'));
      if (entering.length) setTimeout(() => entering.forEach((item) => item.classList.remove('catalog-option-enter')), 220);
      const hiddenCount = extras.filter((item) => item.hidden).length;
      toggle.hidden = false;
      toggle.textContent = !expanded && hiddenCount > 0
        ? `+ ${hiddenCount} ${moreLabel} daha ↓`
        : 'Daha az göster ↑';
    }
    toggle.addEventListener('click', () => { expanded = !expanded; refresh(); });
    container.addEventListener('change', refresh);
    return { refresh };
  }

  function catalogReadState() {
    const genres = [...catalogGenreList.querySelectorAll('input:checked')].map((el) => el.value);
    const providers = [...catalogProviderList.querySelectorAll('input:checked')].map((el) => el.value);
    const rating = catalogRatingList.querySelector('input:checked')?.value || '';
    const runtime = catalogRuntimeList.querySelector('input:checked')?.value || '';
    return {
      query: catalogSearchInput.value.trim(),
      genres,
      yearFrom: catalogYearFrom.value.trim(),
      yearTo: catalogYearTo.value.trim(),
      rating,
      runtime,
      providers,
      language: catalogLanguage.value,
      sort: catalogSort.value,
    };
  }

  function catalogHasActiveFilters(state) {
    return Boolean(state.query || state.genres.length || state.yearFrom || state.yearTo || state.rating || state.runtime || state.providers.length || state.language);
  }

  function catalogGenreLabel(id) {
    const input = catalogGenreList.querySelector(`input[value="${id}"]`);
    return input?.closest('label')?.textContent.trim() || id;
  }

  function renderCatalogSkeletons() {
    catalogGrid.innerHTML = Array.from({ length: 12 })
      .map(() => '<div class="catalog-card"><span class="catalog-card-poster skeleton"></span></div>')
      .join('');
  }

  function renderCatalogMovies(movies) {
    if (!movies.length) {
      catalogGrid.innerHTML = '<div class="catalog-empty"><strong>Eşleşen film bulunamadı.</strong><span>Arama ifadesini sadeleştirmeyi veya bir filtreyi kaldırmayı deneyebilirsin.</span><button type="button" data-catalog-empty-clear>Aramayı ve filtreleri temizle</button></div>';
      return;
    }
    catalogGrid.innerHTML = movies.map((movie) => {
      const rating = movie.rating ? `★ ${Number(movie.rating).toFixed(1)}` : '';
      const meta = [movie.year, rating].filter(Boolean).join('   •   ');
      return `<article class="catalog-card" role="button" tabindex="0" data-movie-id="${movie.id}" aria-label="${escapeHtml(movie.title)} ayrıntılarını aç">
        <span class="catalog-card-poster"><img src="${escapeHtml(movie.poster_url || posterFor(movie))}" alt="${escapeHtml(movie.title)} afişi" loading="lazy" />${movieSaveActionsHtml(movie)}</span>
        <span class="catalog-card-title">${escapeHtml(movie.title)}</span>
        <span class="catalog-card-meta">${escapeHtml(meta)}</span>
      </article>`;
    }).join('');
  }

  function renderCatalogError(message) {
    catalogGrid.innerHTML = `<p class="catalog-error">${escapeHtml(message)}</p>`;
  }

  function renderCatalogPagination() {
    if (catalogTotalPages <= 1) {
      catalogPagination.hidden = true;
      catalogPagination.innerHTML = '';
      return;
    }
    catalogPagination.hidden = false;
    const pages = new Set([1, catalogTotalPages]);
    for (let page = catalogCurrentPage - 2; page <= catalogCurrentPage + 2; page += 1) {
      if (page >= 1 && page <= catalogTotalPages) pages.add(page);
    }
    const sorted = [...pages].sort((a, b) => a - b);
    let html = `<button type="button" data-page="${catalogCurrentPage - 1}" aria-label="Önceki sayfa" ${catalogCurrentPage <= 1 ? 'disabled' : ''}>←</button>`;
    let previous = 0;
    sorted.forEach((page) => {
      if (page - previous > 1) html += '<span class="catalog-pagination-gap">…</span>';
      html += `<button type="button" data-page="${page}" class="${page === catalogCurrentPage ? 'active' : ''}">${page}</button>`;
      previous = page;
    });
    html += `<button type="button" data-page="${catalogCurrentPage + 1}" aria-label="Sonraki sayfa" ${catalogCurrentPage >= catalogTotalPages ? 'disabled' : ''}>→</button>`;
    catalogPagination.innerHTML = html;
  }

  function renderCatalogChips(state) {
    const chips = [];
    if (state.query) {
      chips.push({
        label: `Arama: ${state.query}`,
        clear: () => { catalogSearchInput.value = ''; },
      });
    }
    state.genres.forEach((id) => chips.push({
      label: catalogGenreLabel(id),
      clear: () => { catalogGenreList.querySelector(`input[value="${id}"]`).checked = false; },
    }));
    if (state.yearFrom || state.yearTo) {
      chips.push({
        label: `${state.yearFrom || '…'}–${state.yearTo || '…'}`,
        clear: () => { catalogYearFrom.value = ''; catalogYearTo.value = ''; },
      });
    }
    if (state.rating) {
      chips.push({
        label: `${state.rating}+ ★`,
        clear: () => { catalogRatingList.querySelector('input[value=""]').checked = true; },
      });
    }
    if (state.runtime) {
      chips.push({
        label: CATALOG_RUNTIME_LABELS[state.runtime],
        clear: () => { catalogRuntimeList.querySelector('input[value=""]').checked = true; },
      });
    }
    state.providers.forEach((id) => chips.push({
      label: catalogProviderNames.get(id) || `Platform ${id}`,
      clear: () => {
        const input = catalogProviderList.querySelector(`input[value="${id}"]`);
        if (input) input.checked = false;
      },
    }));
    if (state.language) {
      chips.push({
        label: catalogLanguage.options[catalogLanguage.selectedIndex].textContent,
        clear: () => { catalogLanguage.value = ''; },
      });
    }
    if (!chips.length) {
      catalogChips.hidden = true;
      catalogChips.innerHTML = '';
      return;
    }
    catalogChips.hidden = false;
    catalogChips.innerHTML = chips.map((chip, index) =>
      `<span class="catalog-chip" data-chip-index="${index}">${escapeHtml(chip.label)}<button type="button" aria-label="${escapeHtml(chip.label)} filtresini kaldır">×</button></span>`
    ).join('') + '<button type="button" class="catalog-chips-clear">Tümünü temizle</button>';
    [...catalogChips.querySelectorAll('.catalog-chip button')].forEach((button, index) => {
      button.addEventListener('click', () => { chips[index].clear(); catalogApplyFilters(); });
    });
    catalogChips.querySelector('.catalog-chips-clear')?.addEventListener('click', catalogClearAllFilters);
  }

  async function loadCatalog(page) {
    const state = catalogReadState();
    catalogFiltersClear.hidden = !catalogHasActiveFilters(state);
    renderCatalogChips(state);
    catalogGenreGroup.refresh();
    catalogProviderGroup.refresh();
    renderCatalogSkeletons();
    const token = ++catalogRequestToken;
    try {
      const params = new URLSearchParams({ sort: state.sort, page: String(page) });
      if (state.query) params.set('q', state.query);
      if (state.genres.length) params.set('genres', state.genres.join(','));
      if (state.yearFrom) params.set('year_from', state.yearFrom);
      if (state.yearTo) params.set('year_to', state.yearTo);
      if (state.rating) params.set('rating_min', state.rating);
      if (state.runtime) params.set('runtime', state.runtime);
      if (state.providers.length) params.set('providers', state.providers.join(','));
      if (state.language) params.set('language', state.language);
      const response = await fetch(`/api/catalog?${params}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Filmler yüklenemedi.');
      if (token !== catalogRequestToken) return;
      catalogCurrentPage = data.page || 1;
      catalogTotalPages = data.total_pages || 1;
      renderCatalogMovies(data.movies || []);
      renderCatalogPagination();
      const resultLabel = `${(data.movies || []).length} film`;
      catalogCount.textContent = state.query ? `“${state.query}” · ${resultLabel}` : resultLabel;
      catalogSyncUrl(state, catalogCurrentPage);
    } catch (error) {
      if (token !== catalogRequestToken) return;
      renderCatalogError(error.message);
      catalogPagination.hidden = true;
    }
  }

  function catalogApplyFilters() {
    loadCatalog(1);
  }

  function catalogClearAllFilters() {
    catalogSearchInput.value = '';
    catalogGenreList.querySelectorAll('input:checked').forEach((el) => { el.checked = false; });
    catalogProviderList.querySelectorAll('input:checked').forEach((el) => { el.checked = false; });
    catalogYearFrom.value = '';
    catalogYearTo.value = '';
    catalogRatingList.querySelector('input[value=""]').checked = true;
    catalogRuntimeList.querySelector('input[value=""]').checked = true;
    catalogLanguage.value = '';
    catalogGenreGroup.refresh();
    catalogProviderGroup.refresh();
    catalogApplyFilters();
  }

  function catalogScheduleSearch(rawQuery) {
    clearTimeout(catalogSearchTimer);
    catalogSearchTimer = setTimeout(() => {
      loadCatalog(1);
    }, 400);
  }

  function catalogSyncUrl(state, page) {
    const params = new URLSearchParams();
    if (state.query) params.set('q', state.query);
    if (state.genres.length) params.set('genres', state.genres.join(','));
    if (state.yearFrom) params.set('year_from', state.yearFrom);
    if (state.yearTo) params.set('year_to', state.yearTo);
    if (state.rating) params.set('rating_min', state.rating);
    if (state.runtime) params.set('runtime', state.runtime);
    if (state.providers.length) params.set('providers', state.providers.join(','));
    if (state.language) params.set('language', state.language);
    if (state.sort !== 'popular') params.set('sort', state.sort);
    if (page > 1) params.set('page', String(page));
    const query = params.toString();
    window.history.replaceState(null, '', `${window.location.pathname}${query ? `?${query}` : ''}`);
  }

  function catalogRestoreUrlState() {
    const params = new URLSearchParams(window.location.search);
    catalogSearchInput.value = params.get('q') || '';
    const genreIds = new Set((params.get('genres') || '').split(',').filter(Boolean));
    catalogGenreList.querySelectorAll('input').forEach((input) => { input.checked = genreIds.has(input.value); });
    catalogYearFrom.value = params.get('year_from') || '';
    catalogYearTo.value = params.get('year_to') || '';
    const rating = params.get('rating_min') || '';
    const ratingInput = catalogRatingList.querySelector(`input[value="${rating}"]`) || catalogRatingList.querySelector('input[value=""]');
    if (ratingInput) ratingInput.checked = true;
    const runtime = params.get('runtime') || '';
    const runtimeInput = catalogRuntimeList.querySelector(`input[value="${runtime}"]`) || catalogRuntimeList.querySelector('input[value=""]');
    if (runtimeInput) runtimeInput.checked = true;
    const providerIds = new Set((params.get('providers') || '').split(',').filter(Boolean));
    catalogProviderList.querySelectorAll('input').forEach((input) => { input.checked = providerIds.has(input.value); });
    catalogLanguage.value = params.get('language') || '';
    catalogSort.value = params.get('sort') || 'popular';
    return Math.max(1, Number(params.get('page')) || 1);
  }

  async function loadCatalogProviders() {
    try {
      const response = await fetch('/api/catalog/providers');
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Platformlar yüklenemedi.');
      const providers = data.providers || [];
      providers.forEach((provider) => catalogProviderNames.set(String(provider.id), provider.name));
      // TMDB bu listeyi TR bölgesi için display_priority sırasına göre döndürür;
      // bu yüzden ilk N zaten "en öne çıkan" platformlardır, keyfi değildir.
      catalogProviderList.innerHTML = providers.map((provider, index) => {
        const extra = index >= CATALOG_FEATURED_PROVIDER_COUNT;
        return `<label class="catalog-checkbox${extra ? ' catalog-option-extra' : ''}"${extra ? ' hidden' : ''}><input type="checkbox" name="catalog-provider" value="${provider.id}" />${escapeHtml(provider.name)}</label>`;
      }).join('') || '<p class="catalog-provider-status">Türkiye için platform bulunamadı.</p>';
    } catch (error) {
      catalogProviderList.innerHTML = `<p class="catalog-provider-status">${escapeHtml(error.message)}</p>`;
    }
  }

  function openCatalogFilters() {
    catalogFilters.classList.add('open');
    catalogFiltersBackdrop.hidden = false;
    requestAnimationFrame(() => catalogFiltersBackdrop.classList.add('open'));
  }

  function closeCatalogFilters() {
    catalogFilters.classList.remove('open');
    catalogFiltersBackdrop.classList.remove('open');
    setTimeout(() => { catalogFiltersBackdrop.hidden = true; }, 250);
  }

  catalogGenreList?.addEventListener('change', catalogApplyFilters);
  catalogRatingList?.addEventListener('change', catalogApplyFilters);
  catalogRuntimeList?.addEventListener('change', catalogApplyFilters);
  catalogProviderList?.addEventListener('change', catalogApplyFilters);
  catalogYearFrom?.addEventListener('change', catalogApplyFilters);
  catalogYearTo?.addEventListener('change', catalogApplyFilters);
  catalogLanguage?.addEventListener('change', catalogApplyFilters);
  catalogSort?.addEventListener('change', catalogApplyFilters);
  catalogFiltersClear?.addEventListener('click', catalogClearAllFilters);

  catalogSearchInput?.addEventListener('input', (event) => catalogScheduleSearch(event.target.value));
  catalogSearchForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    clearTimeout(catalogSearchTimer);
    loadCatalog(1);
  });

  catalogGrid.addEventListener('click', (event) => {
    if (event.target.closest('[data-catalog-empty-clear]')) {
      catalogClearAllFilters();
      return;
    }
    const card = event.target.closest('.catalog-card[data-movie-id]');
    if (card) openMovieDetails(card.dataset.movieId);
  });
  catalogGrid.addEventListener('keydown', (event) => {
    if (!['Enter', ' '].includes(event.key)) return;
    const card = event.target.closest('.catalog-card[data-movie-id]');
    if (!card) return;
    event.preventDefault();
    openMovieDetails(card.dataset.movieId);
  });

  catalogPagination?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-page]');
    if (!button || button.disabled) return;
    const page = Number(button.dataset.page);
    if (page >= 1 && page <= catalogTotalPages) {
      loadCatalog(page);
      catalogGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  catalogFiltersToggle?.addEventListener('click', openCatalogFilters);
  catalogFiltersClose?.addEventListener('click', closeCatalogFilters);
  catalogFiltersBackdrop?.addEventListener('click', closeCatalogFilters);

  const catalogGenreGroup = setupCatalogCollapsibleGroup(catalogGenreList, catalogGenreToggle, 'tür');
  const catalogProviderGroup = setupCatalogCollapsibleGroup(catalogProviderList, catalogProviderToggle, 'platform');
  catalogGenreGroup.refresh();

  loadCatalogProviders().finally(() => {
    const initialPage = catalogRestoreUrlState();
    // Restore URL'den seçili gelen gizli türler/platformlar varsa açık kalsın.
    catalogGenreGroup.refresh();
    catalogProviderGroup.refresh();
    loadCatalog(initialPage);
  });
}

// ===== Blog (Seyirci Yazıları): kullanıcı yazıları listesi =====
const blogGrid = document.querySelector('#blog-grid');
if (blogGrid) {
  const blogWriteButton = document.querySelector('#blog-write-button');
  const blogSearchInput = document.querySelector('#blog-search-input');
  const blogMovieFilter = document.querySelector('#blog-movie-filter');
  const blogSortPills = document.querySelector('#blog-sort-pills');
  const blogResultCount = document.querySelector('#blog-result-count');
  const blogSortLabel = document.querySelector('#blog-sort-label');
  const blogViewGridButton = document.querySelector('#blog-view-grid');
  const blogViewListButton = document.querySelector('#blog-view-list');
  const blogPagination = document.querySelector('#blog-pagination');

  const BLOG_SORT_BY_VIEW = { all: 'newest', latest: 'newest', most_read: 'most_read', most_discussed: 'most_discussed' };
  const BLOG_SORT_LABELS = { newest: 'En Yeni', most_read: 'En Çok Okunan', most_discussed: 'En Çok Tartışılan' };
  const BLOG_VIEW_MODE_KEY = 'blog-view-mode';
  const blogInitialParams = new URLSearchParams(window.location.search);
  if (blogSearchInput) blogSearchInput.value = blogInitialParams.get('q') || '';
  let blogPendingMovieId = blogInitialParams.get('movie_id') || '';
  let blogCurrentPage = Number(blogInitialParams.get('page')) || 1;
  let blogActiveView = Object.prototype.hasOwnProperty.call(BLOG_SORT_BY_VIEW, blogInitialParams.get('view') || '')
    ? blogInitialParams.get('view')
    : 'all';
  let blogActiveSort = BLOG_SORT_BY_VIEW[blogActiveView];
  let blogMoviesPopulated = false;
  let blogRequestToken = 0;
  let blogSearchTimer = null;

  function blogSetActivePill(view) {
    blogSortPills?.querySelectorAll('.blog-sort-pill').forEach((pill) => {
      pill.classList.toggle('active', pill.dataset.view === view);
    });
    if (blogSortLabel) blogSortLabel.textContent = `Sıralama: ${BLOG_SORT_LABELS[blogActiveSort] || 'En Yeni'}`;
  }
  blogSetActivePill(blogActiveView);

  function blogSetViewMode(mode) {
    const isList = mode === 'list';
    blogGrid.classList.toggle('is-list', isList);
    blogViewGridButton?.classList.toggle('active', !isList);
    blogViewGridButton?.setAttribute('aria-pressed', String(!isList));
    blogViewListButton?.classList.toggle('active', isList);
    blogViewListButton?.setAttribute('aria-pressed', String(isList));
    try { localStorage.setItem(BLOG_VIEW_MODE_KEY, mode); } catch (_) { /* depolama kapalı olabilir */ }
  }
  let blogStoredViewMode = 'grid';
  try { blogStoredViewMode = localStorage.getItem(BLOG_VIEW_MODE_KEY) || 'grid'; } catch (_) { /* depolama kapalı olabilir */ }
  blogSetViewMode(blogStoredViewMode);
  blogViewGridButton?.addEventListener('click', () => blogSetViewMode('grid'));
  blogViewListButton?.addEventListener('click', () => blogSetViewMode('list'));

  function blogCardHtml(post) {
    const visual = post.movie_backdrop || post.movie_poster || posterFor({ genres: [] });
    const likeIcon = post.is_liked ? '♥' : '♡';
    const authorInitial = escapeHtml((post.author_name || '?').trim().charAt(0).toUpperCase() || '?');
    const editLink = post.is_owner
      ? `<a class="blog-card-edit" href="/blog/${post.id}/duzenle" data-blog-edit>düzenle</a>`
      : '';
    return `<article class="blog-card" role="button" tabindex="0" data-post-id="${post.id}" aria-label="${escapeHtml(post.title)} yazısını aç">
      <span class="blog-card-visual">
        <img src="${escapeHtml(visual)}" alt="${escapeHtml(post.movie_title)} görseli" loading="lazy" />
        <span class="blog-card-type">${escapeHtml(post.post_type || '')}</span>
      </span>
      <span class="blog-card-copy">
        <span class="blog-card-movie-row">
          <span class="blog-card-movie">🎬 <span>${escapeHtml(post.movie_title)}${post.movie_year && post.movie_year !== '—' ? ` · ${escapeHtml(String(post.movie_year))}` : ''}</span></span>
          <button type="button" class="blog-card-save${post.is_saved ? ' active' : ''}" data-blog-save data-post-id="${post.id}" aria-pressed="${post.is_saved}" aria-label="Kaydet">🔖</button>
        </span>
        <h3 class="blog-card-title">${escapeHtml(post.title)}</h3>
        <p class="blog-card-excerpt">${escapeHtml(post.excerpt)}</p>
        <span class="blog-card-footer">
          <span class="blog-card-byline"><span class="blog-card-avatar" aria-hidden="true">${authorInitial}</span><span><strong>${escapeHtml(post.author_name)}</strong> · ${escapeHtml(post.date_label || '')} · ${post.reading_time} dk okuma</span></span>
          <span class="blog-card-stats">
            <button type="button" class="blog-card-stat${post.is_liked ? ' active' : ''}" data-blog-like data-post-id="${post.id}" aria-pressed="${post.is_liked}" aria-label="Beğen">${likeIcon} <span>${post.like_count}</span></button>
            <span class="blog-card-stat" aria-hidden="true">💬 <span>${post.comment_count}</span></span>
            ${editLink}
          </span>
        </span>
      </span>
    </article>`;
  }

  function renderBlogSkeletons() {
    blogGrid.innerHTML = Array.from({ length: 4 }).map(() => '<div class="blog-skeleton-card"></div>').join('');
  }

  function renderBlogEmpty(hasFilters) {
    if (hasFilters) {
      blogGrid.innerHTML = `<div class="blog-state" style="grid-column:1 / -1">
        <span class="blog-state-icon">✎</span>
        <h2>Eşleşen yazı yok.</h2>
        <p>Aramanı ya da film filtresini değiştirip tekrar dene.</p>
        <button class="blog-write-button" type="button" data-blog-clear-filters>Filtreleri temizle</button>
      </div>`;
      return;
    }
    blogGrid.innerHTML = `<div class="blog-state" style="grid-column:1 / -1">
      <span class="blog-state-icon">✎</span>
      <h2>Perde henüz sessiz.</h2>
      <p>İlk film yazısını paylaşan sen ol.</p>
      <button class="blog-write-button" type="button" data-blog-empty-write>İlk yazını yaz →</button>
    </div>`;
  }

  function renderBlogError(message) {
    blogGrid.innerHTML = `<div class="blog-state" style="grid-column:1 / -1">
      <span class="blog-state-icon">!</span>
      <h2>Yazılar şu anda yüklenemiyor.</h2>
      <p>${escapeHtml(message || '')}</p>
      <button class="blog-write-button" type="button" data-blog-retry>Tekrar dene</button>
    </div>`;
  }

  function populateBlogMovieFilter(movies) {
    if (blogMoviesPopulated || !blogMovieFilter) return;
    blogMoviesPopulated = true;
    blogMovieFilter.insertAdjacentHTML('beforeend', movies.map((movie) =>
      `<option value="${movie.id}">${escapeHtml(movie.title)}</option>`
    ).join(''));
    if (blogPendingMovieId) blogMovieFilter.value = blogPendingMovieId;
  }

  function renderBlogPagination(page, totalPages) {
    if (!blogPagination) return;
    if (totalPages <= 1) { blogPagination.hidden = true; blogPagination.innerHTML = ''; return; }
    blogPagination.hidden = false;
    const pages = new Set([1, totalPages]);
    for (let candidate = page - 2; candidate <= page + 2; candidate += 1) {
      if (candidate >= 1 && candidate <= totalPages) pages.add(candidate);
    }
    const sorted = [...pages].sort((a, b) => a - b);
    let html = `<button type="button" data-page="${page - 1}" aria-label="Önceki sayfa" ${page <= 1 ? 'disabled' : ''}>←</button>`;
    let previous = 0;
    sorted.forEach((candidate) => {
      if (candidate - previous > 1) html += '<span class="catalog-pagination-gap">…</span>';
      html += `<button type="button" data-page="${candidate}" class="${candidate === page ? 'active' : ''}">${candidate}</button>`;
      previous = candidate;
    });
    html += `<button type="button" data-page="${page + 1}" aria-label="Sonraki sayfa" ${page >= totalPages ? 'disabled' : ''}>→</button>`;
    blogPagination.innerHTML = html;
  }

  function blogSyncUrl(q, movieId, page, view) {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (movieId) params.set('movie_id', movieId);
    if (view && view !== 'all') params.set('view', view);
    if (page > 1) params.set('page', String(page));
    const query = params.toString();
    window.history.replaceState(null, '', `/blog${query ? `?${query}` : ''}`);
  }

  async function loadBlogPosts(page = 1) {
    renderBlogSkeletons();
    if (blogResultCount) blogResultCount.hidden = true;
    const token = ++blogRequestToken;
    const q = blogSearchInput?.value.trim() || '';
    const movieId = blogMovieFilter?.value || blogPendingMovieId || '';
    blogPendingMovieId = '';
    try {
      const params = new URLSearchParams({ page: String(page), sort: blogActiveSort });
      if (q) params.set('q', q);
      if (movieId) params.set('movie_id', movieId);
      const response = await fetch(`/api/blog/posts?${params}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yazılar yüklenemedi.');
      if (token !== blogRequestToken) return;
      populateBlogMovieFilter(data.movies || []);
      const posts = data.posts || [];
      blogCurrentPage = data.page || 1;
      blogSyncUrl(q, movieId, blogCurrentPage, blogActiveView);
      if (!posts.length) {
        renderBlogEmpty(Boolean(q || movieId));
        if (blogPagination) blogPagination.hidden = true;
        return;
      }
      blogGrid.innerHTML = posts.map(blogCardHtml).join('');
      renderBlogPagination(blogCurrentPage, data.total_pages || 1);
      if (blogResultCount) {
        blogResultCount.hidden = false;
        blogResultCount.textContent = `${data.total} yazı${q ? ` · “${q}”` : ''}`;
      }
    } catch (error) {
      if (token !== blogRequestToken) return;
      renderBlogError(error.message);
      if (blogPagination) blogPagination.hidden = true;
    }
  }

  async function goToWritePost() {
    await authReady;
    if (authState.isAuthenticated) {
      window.location.href = '/blog/yeni';
      return;
    }
    openAuthSaveModal({
      title: 'Sen de perdeye sesini bırak.',
      description: 'Film yazını paylaşmak için giriş yap veya ücretsiz hesap oluştur.',
    });
  }

  async function toggleBlogCardAction(button, kind) {
    await authReady;
    if (!authState.isAuthenticated) { openAuthSaveModal(); return; }
    const postId = button.dataset.postId;
    button.disabled = true;
    try {
      const response = await authFetch(`/api/blog/posts/${postId}/${kind}`, { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'İşlem başarısız.');
      if (kind === 'like') {
        button.classList.toggle('active', data.liked);
        button.setAttribute('aria-pressed', String(data.liked));
        button.innerHTML = `${data.liked ? '♥' : '♡'} <span>${data.like_count}</span>`;
      } else {
        button.classList.toggle('active', data.saved);
        button.setAttribute('aria-pressed', String(data.saved));
      }
    } catch (error) {
      showSavedMovieToast(error.message);
    } finally {
      button.disabled = false;
    }
  }

  blogWriteButton?.addEventListener('click', goToWritePost);
  blogGrid.addEventListener('click', (event) => {
    if (event.target.closest('[data-blog-edit]')) return; // düzenle linki kendi href'iyle gider
    const likeButton = event.target.closest('[data-blog-like]');
    if (likeButton) { toggleBlogCardAction(likeButton, 'like'); return; }
    const saveButton = event.target.closest('[data-blog-save]');
    if (saveButton) { toggleBlogCardAction(saveButton, 'save'); return; }
    if (event.target.closest('[data-blog-empty-write]')) { goToWritePost(); return; }
    if (event.target.closest('[data-blog-retry]')) { loadBlogPosts(blogCurrentPage); return; }
    if (event.target.closest('[data-blog-clear-filters]')) {
      if (blogSearchInput) blogSearchInput.value = '';
      if (blogMovieFilter) blogMovieFilter.value = '';
      loadBlogPosts(1);
      return;
    }
    const card = event.target.closest('.blog-card[data-post-id]');
    if (card) window.location.href = `/blog/${card.dataset.postId}`;
  });
  blogGrid.addEventListener('keydown', (event) => {
    if (!['Enter', ' '].includes(event.key)) return;
    if (event.target.closest('.blog-card-stat') || event.target.closest('[data-blog-edit]')) return;
    const card = event.target.closest('.blog-card[data-post-id]');
    if (!card) return;
    event.preventDefault();
    window.location.href = `/blog/${card.dataset.postId}`;
  });
  blogSearchInput?.addEventListener('input', () => {
    clearTimeout(blogSearchTimer);
    blogSearchTimer = setTimeout(() => loadBlogPosts(1), 300);
  });
  blogMovieFilter?.addEventListener('change', () => loadBlogPosts(1));
  blogSortPills?.addEventListener('click', (event) => {
    const pill = event.target.closest('.blog-sort-pill');
    if (!pill) return;
    blogActiveView = pill.dataset.view;
    blogActiveSort = pill.dataset.sort;
    blogSetActivePill(blogActiveView);
    loadBlogPosts(1);
  });
  blogPagination?.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-page]');
    if (!button || button.disabled) return;
    loadBlogPosts(Number(button.dataset.page));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  loadBlogPosts(blogCurrentPage);
}

// ===== Blog: yazı oluştur/düzenle formu — mevcut TMDB katalog aramasını =====
// ===== (/api/catalog/search) ve authFetch/CSRF akışını reuse eder. =====
const blogForm = document.querySelector('#blog-form');
if (blogForm) {
  const blogFilmSearch = document.querySelector('#blog-film-search');
  const blogFilmResults = document.querySelector('#blog-film-results');
  const blogSelectedMovie = document.querySelector('#blog-selected-movie');
  const blogSelectedPoster = document.querySelector('#blog-selected-poster');
  const blogSelectedTitle = document.querySelector('#blog-selected-title');
  const blogSelectedYear = document.querySelector('#blog-selected-year');
  const blogChangeMovie = document.querySelector('#blog-change-movie');
  const blogTitleInput = document.querySelector('#blog-title-input');
  const blogTypeSelect = document.querySelector('#blog-type-select');
  const blogContentInput = document.querySelector('#blog-content-input');
  const blogFormError = document.querySelector('#blog-form-error');
  const blogFormSubmit = document.querySelector('#blog-form-submit');
  const blogFormCancel = document.querySelector('#blog-form-cancel');

  let blogSelectedMovieData = window.__BLOG_EDITOR_MOVIE__ || null;
  let blogFilmSearchTimer = null;

  function showSelectedMovie(movie) {
    blogSelectedMovieData = movie;
    if (!movie) { blogSelectedMovie.hidden = true; return; }
    blogSelectedPoster.src = movie.poster_url || posterFor({ genres: [] });
    blogSelectedPoster.alt = `${movie.title} afişi`;
    blogSelectedTitle.textContent = movie.title;
    blogSelectedYear.textContent = movie.year || '—';
    blogSelectedMovie.hidden = false;
    blogFilmSearch.value = '';
    blogFilmResults.hidden = true;
  }

  if (blogSelectedMovieData) showSelectedMovie(blogSelectedMovieData);

  function renderBlogFilmResults(movies) {
    if (!movies.length) {
      blogFilmResults.innerHTML = '<p class="blog-film-empty">Eşleşen film bulunamadı.</p>';
      blogFilmResults.hidden = false;
      return;
    }
    blogFilmResults.innerHTML = movies.map((movie) => `<button class="blog-film-result" type="button">
      <img src="${escapeHtml(movie.poster_url || posterFor(movie))}" alt="" />
      <span>${escapeHtml(movie.title)} <small>${escapeHtml(String(movie.year || ''))}</small></span>
    </button>`).join('');
    [...blogFilmResults.querySelectorAll('.blog-film-result')].forEach((button, index) => {
      button.addEventListener('click', () => showSelectedMovie(movies[index]));
    });
    blogFilmResults.hidden = false;
  }

  blogFilmSearch?.addEventListener('input', (event) => {
    const value = event.target.value.trim();
    clearTimeout(blogFilmSearchTimer);
    if (value.length < 2) { blogFilmResults.hidden = true; return; }
    blogFilmSearchTimer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/catalog/search?q=${encodeURIComponent(value)}`);
        const data = await response.json();
        renderBlogFilmResults(data.movies || []);
      } catch (_) {
        blogFilmResults.innerHTML = '<p class="blog-film-empty">Filmler yüklenemedi.</p>';
        blogFilmResults.hidden = false;
      }
    }, 350);
  });

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.blog-film-picker')) blogFilmResults.hidden = true;
  });

  blogChangeMovie?.addEventListener('click', () => showSelectedMovie(null));

  blogFormCancel?.addEventListener('click', () => {
    const mode = blogForm.dataset.editorMode;
    const postId = blogForm.dataset.postId;
    window.location.href = mode === 'edit' && postId ? `/blog/${postId}` : '/blog';
  });

  blogForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    blogFormError.textContent = '';
    if (!blogSelectedMovieData) { blogFormError.textContent = 'Bir film seçmelisin.'; return; }
    const postType = blogTypeSelect?.value || '';
    if (!postType) { blogFormError.textContent = 'Bir yazı türü seçmelisin.'; return; }
    const title = blogTitleInput.value.trim();
    if (!title) { blogFormError.textContent = 'Yazına bir başlık eklemelisin.'; return; }
    const content = blogContentInput.value.trim();
    if (!content) { blogFormError.textContent = 'Yazı alanı boş bırakılamaz.'; return; }

    const mode = blogForm.dataset.editorMode;
    const postId = blogForm.dataset.postId;
    const url = mode === 'edit' && postId ? `/api/blog/posts/${postId}` : '/api/blog/posts';
    const method = mode === 'edit' && postId ? 'PUT' : 'POST';
    blogFormSubmit.disabled = true;
    try {
      const response = await authFetch(url, {
        method, headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ movie: blogSelectedMovieData, post_type: postType, title, content }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yazı kaydedilemedi.');
      window.location.href = `/blog/${data.post.id}`;
    } catch (error) {
      blogFormError.textContent = error.message;
      blogFormSubmit.disabled = false;
    }
  });
}

// ===== Blog: yazı detay sayfası — sahibi için sil aksiyonu, film linki, beğeni/kaydet =====
const blogPostDeleteButton = document.querySelector('#blog-post-delete');
if (blogPostDeleteButton) {
  blogPostDeleteButton.addEventListener('click', async () => {
    if (!window.confirm('Bu yazıyı silmek istediğine emin misin? Bu işlem geri alınamaz.')) return;
    const postId = blogPostDeleteButton.dataset.postId;
    blogPostDeleteButton.disabled = true;
    try {
      const response = await authFetch(`/api/blog/posts/${postId}`, { method: 'DELETE' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yazı silinemedi.');
      window.location.href = blogPostDeleteButton.dataset.next || '/blog';
    } catch (error) {
      window.alert(error.message);
      blogPostDeleteButton.disabled = false;
    }
  });
}

const blogPostMovieButton = document.querySelector('.blog-post-movie[data-movie-id]');
blogPostMovieButton?.addEventListener('click', () => openMovieDetails(blogPostMovieButton.dataset.movieId));

const blogPostLikeButton = document.querySelector('#blog-post-like');
blogPostLikeButton?.addEventListener('click', async () => {
  await authReady;
  if (!authState.isAuthenticated) { openAuthSaveModal(); return; }
  const postId = blogPostLikeButton.dataset.postId;
  blogPostLikeButton.disabled = true;
  try {
    const response = await authFetch(`/api/blog/posts/${postId}/like`, { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'İşlem başarısız.');
    blogPostLikeButton.classList.toggle('active', data.liked);
    document.querySelector('#blog-post-like-icon').textContent = data.liked ? '♥' : '♡';
    document.querySelector('#blog-post-like-count').textContent = data.like_count;
  } catch (error) {
    showSavedMovieToast(error.message);
  } finally {
    blogPostLikeButton.disabled = false;
  }
});

const blogPostSaveButton = document.querySelector('#blog-post-save');
blogPostSaveButton?.addEventListener('click', async () => {
  await authReady;
  if (!authState.isAuthenticated) { openAuthSaveModal(); return; }
  const postId = blogPostSaveButton.dataset.postId;
  blogPostSaveButton.disabled = true;
  try {
    const response = await authFetch(`/api/blog/posts/${postId}/save`, { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'İşlem başarısız.');
    blogPostSaveButton.classList.toggle('active', data.saved);
    document.querySelector('#blog-post-save-label').textContent = data.saved ? 'Kaydedildi' : 'Kaydet';
  } catch (error) {
    showSavedMovieToast(error.message);
  } finally {
    blogPostSaveButton.disabled = false;
  }
});

// ===== Blog: yazı detayı altındaki yorumlar (liste + oluştur + kendi yorumunu sil) =====
const blogCommentsSection = document.querySelector('.blog-comments[data-post-id]');
if (blogCommentsSection) {
  const blogCommentsList = document.querySelector('#blog-comments-list');
  const blogCommentsCount = document.querySelector('#blog-comments-count');
  const blogCommentForm = document.querySelector('#blog-comment-form');
  const blogCommentInput = document.querySelector('#blog-comment-input');
  const blogCommentError = document.querySelector('#blog-comment-error');
  const commentsPostId = blogCommentsSection.dataset.postId;

  function blogCommentHtml(comment) {
    const deleteButton = comment.is_owner
      ? `<button type="button" data-delete-comment-id="${comment.id}">Sil</button>`
      : '';
    return `<article class="blog-comment">
      <div class="blog-comment-head"><strong>${escapeHtml(comment.author_name)}</strong><span>${escapeHtml(comment.date_label || '')}</span>${deleteButton}</div>
      <p>${escapeHtml(comment.content)}</p>
    </article>`;
  }

  async function loadBlogComments() {
    blogCommentsList.innerHTML = '<p class="blog-comments-empty">Yorumlar yükleniyor…</p>';
    try {
      const response = await fetch(`/api/blog/posts/${commentsPostId}/comments`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yorumlar yüklenemedi.');
      const comments = data.comments || [];
      if (blogCommentsCount) blogCommentsCount.textContent = `(${comments.length})`;
      blogCommentsList.innerHTML = comments.length
        ? comments.map(blogCommentHtml).join('')
        : '<p class="blog-comments-empty">Henüz yorum yok. İlk yorumu sen yap.</p>';
    } catch (error) {
      blogCommentsList.innerHTML = `<p class="blog-comments-empty">${escapeHtml(error.message)}</p>`;
    }
  }

  blogCommentsList.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-delete-comment-id]');
    if (!button) return;
    if (!window.confirm('Bu yorumu silmek istediğine emin misin?')) return;
    try {
      const response = await authFetch(`/api/blog/comments/${button.dataset.deleteCommentId}`, { method: 'DELETE' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yorum silinemedi.');
      loadBlogComments();
    } catch (error) {
      window.alert(error.message);
    }
  });

  blogCommentForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    blogCommentError.textContent = '';
    await authReady;
    if (!authState.isAuthenticated) { openAuthSaveModal(); return; }
    const content = blogCommentInput.value.trim();
    if (!content) { blogCommentError.textContent = 'Yorum boş olamaz.'; return; }
    const submitButton = blogCommentForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
      const response = await authFetch(`/api/blog/posts/${commentsPostId}/comments`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Yorum gönderilemedi.');
      blogCommentInput.value = '';
      loadBlogComments();
    } catch (error) {
      blogCommentError.textContent = error.message;
    } finally {
      submitButton.disabled = false;
    }
  });

  loadBlogComments();
}
