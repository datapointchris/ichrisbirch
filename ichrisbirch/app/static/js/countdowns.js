function updateDaysLeft(dateString, elementId) {
  // Convert the date string to a JavaScript Date object
  var date = new Date(dateString);

  // Get today's date
  var today = new Date();

  // Calculate the difference in milliseconds
  var differenceMs = date - today;

  // Convert the difference to days
  var days = Math.floor(differenceMs / (1000 * 60 * 60 * 24));

  // Update the element with the number of days left
  var element = document.getElementById(elementId);
  element.textContent = days + " Days Left";

  // Add color classes based on the number of days remaining
  if (days < 14) {
    element.classList.add("two-weeks-left");
  } else if (days < 30) {
    element.classList.add("month-left");
  }
}
