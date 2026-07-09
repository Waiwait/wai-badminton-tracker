buttonClickHandler = {
    '.finish-match-btn': showConfirmScore,
    '.cancel-score-btn': hideConfirmScore,
    '.submit-score-btn': hideConfirmScore,
}

document.addEventListener('click', (e) => {
    for (const [selector, handler] of Object.entries(buttonClickHandler)) {
        if (e.target.matches(selector)) {
            handler(e.target);
            break;
        }
    }
});

function showConfirmScore(button) {
    const confirmScore = button.nextElementSibling;
    const body = document.querySelector('body');

    if (!confirmScore?.classList.contains('confirm-score')) {
        console.log('Confirm score element not found');
        return;
    }

    body.classList.add('overflow-hidden');

    const scores = button.previousElementSibling;
    const team1Score = scores.querySelector('input[name="team1_score"]') ? scores.querySelector('input[name="team1_score"]').value : 0;
    const team2Score = scores.querySelector('input[name="team2_score"]') ? scores.querySelector('input[name="team2_score"]').value : 0;
    const courtNumber = button.getAttribute('data-court-number') || '';

    const scoreText = confirmScore.querySelector('.score-text').innerText = `Submit the score ${team1Score} - ${team2Score} for court ${courtNumber}`;
    confirmScore.classList.replace('hidden', 'visible');
}

function hideConfirmScore(button) {
    const confirmScore = button.closest('.confirm-score');
    const body = document.querySelector('body');

    if (!confirmScore) {
        console.log('Confirm score element not found');
        return;
    }

    confirmScore.classList.replace('visible', 'hidden');
    body.classList.remove('overflow-hidden');
}