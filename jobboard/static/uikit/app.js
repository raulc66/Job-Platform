// Simple close for alerts
window.addEventListener('click', (e) => {
  if (e.target.matches('.alert__close')) {
    e.target.closest('.alert').remove();
  }
});
