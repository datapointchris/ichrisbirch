function updateDaysLeft(dateString, elementId) {
  const date = new Date(dateString);
  const today = new Date();
  const differenceMs = date - today;

  if (differenceMs <= 0) {
    const element = document.getElementById(elementId);
    element.textContent = 'Past';
    element.classList.add('past');
    return;
  }

  let differenceDays = Math.floor(differenceMs / 86400000);
  const remainingTime = [];

  if (differenceDays > 365) {
    const years = Math.floor(differenceDays / 365);
    remainingTime.push(years + (years > 1 ? ' years' : ' year'));
    differenceDays %= 365;
  }

  if (differenceDays > 30) {
    const months = Math.floor(differenceDays / 30);
    remainingTime.push(months + (months > 1 ? ' months' : ' month'));
    differenceDays %= 30;
  }

  if (differenceDays >= 7) {
    const weeks = Math.floor(differenceDays / 7);
    remainingTime.push(weeks + (weeks > 1 ? ' weeks' : ' week'));
    differenceDays %= 7;
  }

  if (differenceDays > 0) {
    remainingTime.push(differenceDays + (differenceDays > 1 ? ' days' : ' day'));
  }

  const message = remainingTime.join(', ');

  const element = document.getElementById(elementId);
  element.textContent = message;

  const daysRemaining = Math.floor(differenceMs / 86400000);
  if (daysRemaining < 14) {
    element.classList.add('two-weeks-left');
  } else if (daysRemaining < 30) {
    element.classList.add('month-left');
  }
}
