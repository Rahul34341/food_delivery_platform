// FoodieExpress - Forgot Password

const forgotPasswordForm = document.getElementById("forgotPasswordForm");

if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value.trim();
        const messageElement = document.getElementById("forgotMessage");
        const button = forgotPasswordForm.querySelector(
            "button[type='submit']"
        );

        button.disabled = true;
        button.textContent = "Sending Request...";

        messageElement.className = "message";
        messageElement.textContent = "";

        try {
            const response = await API.post(
                FOODIE_CONFIG.ENDPOINTS.FORGOT_PASSWORD,
                { email: email }
            );

            messageElement.className = "message success";
            messageElement.textContent =
                response.message || "If the email is registered, password reset instructions will be provided.";

            // Development only: backend may return a reset token.
            if (response.reset_token) {
                const tokenText = document.createElement("p");
                tokenText.textContent =
                    "Development reset token: " + response.reset_token;
                tokenText.style.marginTop = "10px";
                tokenText.style.overflowWrap = "anywhere";
                messageElement.appendChild(tokenText);
            }

            forgotPasswordForm.reset();

        } catch (error) {
            messageElement.className = "message error";
            messageElement.textContent =
                error.message || "Unable to process your request.";
        } finally {
            button.disabled = false;
            button.textContent = "Request Reset";
        }
    });
}
