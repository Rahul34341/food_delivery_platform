
// FoodieExpress - Reset Password

const resetPasswordForm = document.getElementById("resetPasswordForm");

if (resetPasswordForm) {
    resetPasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const token = document.getElementById("token").value.trim();
        const newPassword =
            document.getElementById("new_password").value;
        const confirmPassword =
            document.getElementById("confirm_password").value;

        const messageElement = document.getElementById("resetMessage");
        const button = resetPasswordForm.querySelector(
            "button[type='submit']"
        );

        if (newPassword !== confirmPassword) {
            messageElement.className = "message error";
            messageElement.textContent =
                "New password and confirm password do not match.";
            return;
        }

        button.disabled = true;
        button.textContent = "Resetting Password...";

        try {
            const response = await API.post(
                FOODIE_CONFIG.ENDPOINTS.RESET_PASSWORD,
                {
                    token: token,
                    new_password: newPassword
                }
            );

            messageElement.className = "message success";
            messageElement.textContent =
                response.message ||
                "Password reset successfully. Please log in with your new password.";

            resetPasswordForm.reset();

            setTimeout(() => {
                window.location.href = "../login.html";
            }, 2500);

        } catch (error) {
            messageElement.className = "message error";
            messageElement.textContent =
                error.message || "Unable to reset password.";
        } finally {
            button.disabled = false;
            button.textContent = "Reset Password";
        }
    });
}
