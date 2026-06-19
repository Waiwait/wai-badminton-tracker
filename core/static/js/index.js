buttonClickHandler = {
    '.finish-match-btn': showConfirmScore,
    '.cancel-score-btn': hideConfirmScore
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

    if (!confirmScore?.classList.contains('confirm-score')) {
        console.log('Confirm score element not found');
        return;
    }

    const scores = button.previousElementSibling;
    const team1Score = scores.querySelector('input[name="team1_score"]') ? scores.querySelector('input[name="team1_score"]').value : 0;
    const team2Score = scores.querySelector('input[name="team2_score"]') ? scores.querySelector('input[name="team2_score"]').value : 0;

    const scoreText = confirmScore.querySelector('.score-text').innerText = `Submit the score ${team1Score} - ${team2Score}`;
    confirmScore.classList.replace('invisible', 'visible');
}

function hideConfirmScore(button) {
    const confirmScore = button.closest('.confirm-score');

    if (!confirmScore) {
        console.log('Confirm score element not found');
        return;
    }

    confirmScore.classList.replace('visible', 'invisible');
}