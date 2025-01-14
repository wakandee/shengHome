const container = document.getElementById('accountContainer');
const registerBtn= document.getElementById('register');
const loginBtn= document.getElementById('login');

registerBtn.addEventListener('click', ()=>{
    container.classList.add('active');
});

loginBtn.addEventListener('click', ()=>{
    container.classList.remove('active');
});


const darkModeToggleCheckbox = document.getElementById('darkmode_toggle_checkbox');

darkModeToggleCheckbox.addEventListener('change', () => {
  if (darkModeToggleCheckbox.checked) {
    document.body.classList.add('dark_mode');
  } else {
    document.body.classList.remove('dark_mode');
  }
});


    // Flash message functionality
    document.addEventListener("DOMContentLoaded", function () {
        const flashMessages = document.querySelectorAll(".flash-overlay");

        flashMessages.forEach((message) => {
            const closeBtn = message.querySelector(".close-btn");

            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                message.style.opacity = "0";
                setTimeout(() => message.remove(), 500);
            }, 3000);

            // Close button functionality
            closeBtn.addEventListener("click", () => {
                message.style.opacity = "0";
                setTimeout(() => message.remove(), 500);
            });
        });
    });