// FoodieExpress - Change Password

const changePasswordForm = document.getElementById("changePasswordForm");

function showPasswordMessage(message, type) {
    const element = document.getElementById("passwordMessage");
    element.textContent = message;
    element.className = `message ${type}`;
}

if (changePasswordForm) {
    changePasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const currentPassword =
            document.getElementById("current_password").value;

        const newPassword =
            document.getElementById("new_password").value;

        const confirmPassword =
            document.getElementById("confirm_password").value;

        if (newPassword !== confirmPassword) {
            showPasswordMessage(
                "New password and confirm password do not match.",
                "error"
            );
            return;
        }

        if (currentPassword === newPassword) {
            showPasswordMessage(
                "New password must be different from the current password.",
                "error"
            );
            return;
        }

        const button = changePasswordForm.querySelector(
            "button[type='submit']"
        );

        button.disabled = true;
        button.textContent = "Updating Password...";

        try {
            const response = await API.request(
                FOODIE_CONFIG.ENDPOINTS.CHANGE_PASSWORD,
                {
                    method: "PUT",
                    body: {
                        current_password: currentPassword,
                        new_password: newPassword
                    }
                }
            );

            showPasswordMessage(
                response.message || "Password changed successfully. Please log in again.",
                "success"
            );

            changePasswordForm.reset();

            // Backend revokes all active sessions after password change.
            API.clearTokens();
            sessionStorage.removeItem("foodie_user");

            setTimeout(() => {
                window.location.href = "../login.html";
            }, 2000);

        } catch (error) {
            showPasswordMessage(
                error.message || "Unable to change password.",
                "error"
            );
        } finally {
            button.disabled = false;
            button.textContent = "Update Password";
        }
    });
}
