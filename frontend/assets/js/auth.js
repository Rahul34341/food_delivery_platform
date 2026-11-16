// FoodieExpress Authentication

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);

    if (!element) return;

    element.textContent = message;
    element.className = `message ${type}`;
}

// ---------------- LOGIN ----------------

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const button = loginForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.textContent = "Logging in...";

        try {
            const response = await API.post(
                FOODIE_CONFIG.ENDPOINTS.LOGIN,
                { email, password }
            );

            API.setTokens(response);

            sessionStorage.setItem(
                "foodie_user",
                JSON.stringify(response.user)
            );

            showMessage(
                "loginMessage",
                "Login successful! Redirecting...",
                "success"
            );

            window.location.href = "dashboard.html";

        } catch (error) {
            showMessage("loginMessage", error.message, "error");
        } finally {
            button.disabled = false;
            button.textContent = "Login";
        }
    });
}

// ---------------- REGISTRATION ----------------

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const userData = {
            username: document.getElementById("username").value.trim(),
            full_name: document.getElementById("full_name").value.trim(),
            email: document.getElementById("email").value.trim(),
            phone: document.getElementById("phone").value.trim() || null,
            password: document.getElementById("password").value,
            role: document.getElementById("role").value
        };

        const button = registerForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.textContent = "Creating Account...";

        try {
            const response = await API.post(
                FOODIE_CONFIG.ENDPOINTS.REGISTER,
                userData
            );

            showMessage(
                "registerMessage",
                "Registration successful! Redirecting to login...",
                "success"
            );

            registerForm.reset();

            setTimeout(() => {
                window.location.href = "login.html";
            }, 1500);

        } catch (error) {
            showMessage(
                "registerMessage",
                error.message || "Registration failed.",
                "error"
            );
        } finally {
            button.disabled = false;
            button.textContent = "Create Account";
        }
    });
}
