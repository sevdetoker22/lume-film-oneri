const form = document.querySelector('#search-form');
const query = document.querySelector('#query');
const button = form.querySelector('button');
const result = document.querySelector('#result');
const answer = document.querySelector('#answer');
const matches = document.querySelector('#matches');
const quizButton = document.querySelector('#quiz-button');
const quiz = document.querySelector('#quiz');
const quizCategory = document.querySelector('#quiz-category');
const quizQuestion = document.querySelector('#quiz-question');
const quizChoices = document.querySelector('#quiz-choices');
const quizFeedback = document.querySelector('#quiz-feedback');
const nextQuestion = document.querySelector('#next-question');
const currentTime = document.querySelector('#current-time');
const moodForm = document.querySelector('#mood-form');
const moodInput = document.querySelector('#mood-input');
const recommendations = document.querySelector('#recommendations');
const surveyModal = document.querySelector('#survey-modal');
const surveyProgress = document.querySelector('#survey-progress');
const surveyTitle = document.querySelector('#survey-title');
const surveyQuestion = document.querySelector('#survey-question');
const surveyOptions = document.querySelector('#survey-options');
const secretCard = document.querySelector('#secret-card');
const surveyDemographics = document.querySelector('#survey-demographics');
const surveyAge = document.querySelector('#survey-age');
const genderOptions = document.querySelector('#gender-options');
const demographicsNext = document.querySelector('#survey-demographics-next');
const surveyResult = document.querySelector('#survey-result');
const surveyBox = document.querySelector('.survey-box');
const surveyClose = document.querySelector('#survey-close');
const mainPage = document.querySelector('#main-page');
const columnPage = document.querySelector('#column-page');
const columnNav = document.querySelector('#column-nav');
const columnBack = document.querySelector('#column-back');
const zodiacNav = document.querySelector('#zodiac-nav');
const zodiacLabel = document.querySelector('#zodiac-label');
const zodiacTitle = document.querySelector('#zodiac-title');
const zodiacCaption = document.querySelector('#zodiac-caption');
const zodiacMovies = document.querySelector('#zodiac-movies');
const featuredPoster = document.querySelector('#featured-poster');
const featuredTitle = document.querySelector('#featured-title');
const featuredMeta = document.querySelector('#featured-meta');
const featuredNote = document.querySelector('#featured-note');
let currentQuiz = null;

const soundToggle = document.querySelector('.sound-toggle');
soundToggle?.addEventListener('click', () => {
  const isOn = soundToggle.getAttribute('aria-pressed') === 'true';
  soundToggle.setAttribute('aria-pressed', String(!isOn));
  soundToggle.lastChild.textContent = !isOn ? ' Ambiyans açık' : ' Ambiyans kapalı';
});

surveyClose.addEventListener('click', () => { surveyModal.hidden = true; });

function updateClock() {
  currentTime.textContent = new Intl.DateTimeFormat('tr-TR', {
    hour: '2-digit', minute: '2-digit'
  }).format(new Date());
}

function posterFor(movie) {
  const genres = (movie.genres || []).join(' ').toLowerCase();
  if (genres.includes('animasyon') || genres.includes('aile')) return '/static/images/trivia-tv.png';
  if (genres.includes('romantik') || genres.includes('komedi')) return '/static/images/trivia-music.png';
  return '/static/images/trivia-film.png';
}

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

function showColumnPage() {
  mainPage.hidden = true;
  columnPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'auto' });
  loadZodiac('Koç');
}

function hideColumnPage() {
  columnPage.hidden = true;
  mainPage.hidden = false;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadZodiac(zodiac) {
  const [title, caption] = zodiacCopy[zodiac];
  zodiacLabel.textContent = `${zodiac.toUpperCase()} İÇİN FİLM GECESİ`;
  zodiacTitle.textContent = title;
  zodiacCaption.textContent = caption;
  zodiacNav.querySelectorAll('button').forEach((item) => item.classList.toggle('active', item.dataset.zodiac === zodiac));
  zodiacMovies.innerHTML = '<p class="column-loading">Seçkin hazırlanıyor…</p>';
  try {
    const response = await fetch('/api/zodiac-recommend', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ zodiac })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Seçki hazırlanamadı.');
    zodiacMovies.innerHTML = data.movies.map((movie) => '<article class="column-movie"><img src="' + (movie.poster_url || posterFor(movie)) + '" alt="' + escapeHtml(movie.title) + ' afişi" /><div class="column-movie-copy"><h3>' + escapeHtml(movie.title) + '</h3><p class="column-meta">' + escapeHtml(movie.year) + ' · ' + escapeHtml(movie.genres.join(' · ')) + (movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : '') + '</p><p>' + escapeHtml(movie.note) + '</p></div></article>').join('');
  } catch (error) {
    zodiacMovies.innerHTML = '<p class="column-loading">' + escapeHtml(error.message) + '</p>';
  }
}

columnNav.addEventListener('click', (event) => { event.preventDefault(); showColumnPage(); });
columnBack.addEventListener('click', hideColumnPage);
zodiacNav.addEventListener('click', (event) => {
  const zodiac = event.target.closest('[data-zodiac]')?.dataset.zodiac;
  if (zodiac) loadZodiac(zodiac);
});

function updateFeatured(movie) {
  if (!movie || !featuredPoster) return;
  featuredPoster.src = posterFor(movie);
  featuredPoster.alt = movie.title;
  featuredTitle.textContent = movie.title;
  featuredMeta.textContent = `${movie.year} · ${movie.genres.join(' · ')}`;
  featuredNote.textContent = movie.note;
}

function renderMovieCards(movies) {
  recommendations.innerHTML = movies.map((movie) => `<article class="recommendation">
    <div class="poster-art"><img src="${movie.poster_url || posterFor(movie)}" alt="${escapeHtml(movie.title)} afişi" /></div>
    <h3>${escapeHtml(movie.title)} <span class="meta">${movie.year}</span></h3>
    <p>${escapeHtml(movie.note)}</p><small class="movie-genre">${escapeHtml(movie.genres.join(' · '))}${movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : ''}</small>
  </article>`).join('');
  updateFeatured(movies[0]);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const value = query.value.trim();
  if (value.length < 2) return;
  query.value = '';
  button.disabled = true;
  button.querySelector('span').textContent = '…';
  answer.textContent = 'Aranıyor… İlk sorguda yerel model indirilebilir; bu birkaç dakika sürebilir.';
  result.hidden = false;
  matches.innerHTML = '';
  try {
    const response = await fetch('/api/search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: value }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Arama gerçekleştirilemedi.');
    answer.textContent = data.answer;
    document.querySelector('.result-label').textContent = 'LÛME ÖNERİSİ · YEREL LLM';
    matches.innerHTML = data.matches.map(({ question, answer }) => `<article class="match"><b>${escapeHtml(question)}</b><br>${escapeHtml(answer)}</article>`).join('');
  } catch (error) {
    answer.textContent = error.message;
  } finally {
    button.disabled = false;
    button.querySelector('span').textContent = '→';
  }
});

function escapeHtml(value) {
  const element = document.createElement('span');
  element.textContent = value;
  return element.innerHTML;
}

quizButton.addEventListener('click', loadQuiz);
nextQuestion.addEventListener('click', loadQuiz);

async function loadQuiz() {
  quiz.hidden = false;
  quizButton.disabled = true;
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
  buttons.forEach((button) => { button.disabled = true; });
  try {
    const response = await fetch('/api/quiz/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentQuiz.id, choice })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Cevap kontrol edilemedi.');
    const correctButton = buttons.find((button) => button.dataset.value === data.answer);
    if (correctButton) correctButton.classList.add('correct');
    if (!data.correct) selectedButton.classList.add('incorrect');
    quizFeedback.innerHTML = data.correct ? '<strong>Doğru cevap.</strong> Tebrikler!' : `Doğru cevap: <strong>${escapeHtml(data.answerDisplay)}</strong>`;
    quizFeedback.hidden = false;
    nextQuestion.hidden = false;
  } catch (error) {
    currentQuiz.answered = false;
    buttons.forEach((button) => { button.disabled = false; });
    quizFeedback.textContent = error.message;
    quizFeedback.hidden = false;
  }
}

updateClock();
setInterval(updateClock, 30_000);

moodForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mood = moodInput.value.trim();
  if (mood.length < 2) return;
  moodInput.value = '';
  recommendations.textContent = 'Sana uygun filmler aranıyor…';
  try {
    const response = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Öneriler getirilemedi.');
    renderMovieCards(data.recommendations);
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
  surveyProgress.textContent = `${surveyStep + 1} / 5`;
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
  demographicsNext.disabled = !surveyAge.value;
}

genderOptions.querySelectorAll('button').forEach((item) => item.addEventListener('click', () => selectGender(item.dataset.gender)));
surveyAge.addEventListener('input', () => { demographicsNext.disabled = !surveyAge.value; });
demographicsNext.addEventListener('click', () => {
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
    const poster = movie.poster_url || posterFor(movie);
    const rating = movie.rating ? ` · ★ ${Number(movie.rating).toFixed(1)}` : '';
    secretCard.innerHTML = '<div class="secret-poster"><img src="' + poster + '" alt="' + escapeHtml(movie.title) + ' afişi" /></div>' +
      '<p class="secret-eyebrow">BUGÜNE ÖZEL</p><h3>' + escapeHtml(movie.title) + ' <span class="meta">' + movie.year + '</span></h3>' +
      '<p class="secret-meta">' + escapeHtml(movie.genres.join(' · ')) + rating + '</p><p class="secret-note">' + escapeHtml(movie.note) + '</p>';
    secretCard.hidden = false;
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
  surveyResult.innerHTML = '<p class="survey-result-label">BUGÜNE ÖZEL</p><div class="survey-result-grid"><div class="survey-result-poster"><img src="' + poster + '" alt="' + escapeHtml(movie.title) + ' afişi" /></div><div><h2>' + escapeHtml(movie.title) + '</h2><p class="survey-result-meta">' + escapeHtml(movie.year) + ' · ' + escapeHtml(movie.genres.join(' · ')) + rating + '</p><p class="survey-result-reason">' + escapeHtml(reason) + '</p><div class="survey-result-actions"><button type="button" data-survey-action="discover">Filmi keşfet</button><button class="secondary" type="button" data-survey-action="home">Ana sayfaya geç →</button></div></div></div>';
}

surveyResult.addEventListener('click', (event) => {
  const action = event.target.closest('[data-survey-action]')?.dataset.surveyAction;
  if (!action) return;
  surveyModal.hidden = true;
  if (action === 'discover') secretCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  if (action === 'home') window.scrollTo({ top: 0, behavior: 'smooth' });
});

renderSurvey();
