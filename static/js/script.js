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