
if('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker Registered'))
            .catch(err => console.error('SW Registration Failed:', err));
    });
}


document.addEventListener('DOMContentLoaded', () => {
    
   
    const loginForm = document.getElementById('LoginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            const btn = document.querySelector('.primary-btn');

            const originalText = btn.innerText;
            btn.innerText = "Verifying...";
            btn.disabled = true;

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: phone, password: password })
                });

                const result = await response.json();

                if (result.success) {
                    alert("Welcome " + result.user + "!");
                    window.location.href = '/dashboard';
               
                } else {
                    alert(result.message);
                }
            } catch (error) {
                console.error(error);
                alert("Server connection failed.");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }

   
    const signupForm = document.getElementById('authForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            
            const fullName = document.querySelector('input[placeholder="Full Name"]').value;
            const dob = document.getElementById('dob').value;
            const phone = document.querySelector('input[type="tel"]').value;
            const password = document.getElementById('pass').value;
            const confirmPass = document.getElementById('confirmPass').value;
            const captchaInput = document.getElementById('captchaInput').value;
            const captchaCode = document.getElementById('captchaCode').innerText;
            const btn = document.querySelector('.register-btn');

          
            if (password !== confirmPass) {
                alert("Passwords do not match!");
                return;
            }
            if (captchaInput !== captchaCode) {
                alert("Incorrect Captcha!");
                return;
            }

            const originalText = btn.innerText;
            btn.innerText = "Creating Account...";
            btn.disabled = true;

            try {
                const response = await fetch('/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        full_name: fullName,
                        phone: phone,
                        password: password,
                        dob: dob
                    })
                });

                const result = await response.json();

                if (result.success) {
                    alert(result.message);
                    window.location.href = '/dashboard'; 
                } else {
                    alert(result.message);
                }
            } catch (error) {
                console.error(error);
                alert("Server connection failed.");
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});

function generateCaptcha() {
    const chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let captcha = '';
    for (let i = 0; i < 6; i++) {
        captcha += chars[Math.floor(Math.random() * chars.length)];
    }
    const captchaDisplay = document.getElementById('captchaCode');
    if(captchaDisplay) captchaDisplay.innerText = captcha;
}