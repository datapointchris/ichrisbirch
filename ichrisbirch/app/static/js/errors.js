var container = document.querySelector('#error-container');

// Define the speed of the movement
var speedX = Math.random() * 10;
var speedY = Math.random() * 10;

// Set the initial position of the container to the center of the viewport
var newX = window.innerWidth / 2;
var newY = window.innerHeight / 2;
container.style.transform = `translate(${newX}px, ${newY}px)`;

function animate() {
    // Get the container's current position and size
    var rect = container.getBoundingClientRect();

    // Calculate the container's new position
    newX += speedX;
    newY += speedY;

    // Check if the container hit the edge of the viewport
    if (newX < 0 || newX + rect.width > window.innerWidth) {
        // Reverse the direction of movement
        speedX = -speedX;
        // Adjust newX to be within the viewport
        newX = newX < 0 ? 0 : window.innerWidth - rect.width;
    }
    if (newY < 0 || newY + rect.height > window.innerHeight - 50) { // Subtract the size of the scrollbar
        // Reverse the direction of movement
        speedY = -speedY;
        // Adjust newY to be within the viewport
        newY = newY < 0 ? 0 : window.innerHeight - rect.height - 50; // Subtract the size of the scrollbar
    }

    // Apply the new position to the container
    container.style.transform = `translate(${newX}px, ${newY}px)`;

    // Request the next animation frame
    requestAnimationFrame(animate);
}

// Start the animation
animate();
