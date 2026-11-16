// FoodieExpress Profile Management

document.addEventListener("DOMContentLoaded", async function () {
    if (!API.getAccessToken()) {
        window.location.href = "login.html";
        return;
    }

    try {
        const user = await API.get(FOODIE_CONFIG.ENDPOINTS.PROFILE);

        document.getElementById("username").value = user.username || "";
        document.getElementById("full_name").value = user.full_name || "";
        document.getElementById("email").value = user.email || "";
        document.getElementById("phone").value = user.phone || "";

    } catch (error) {
        API.clearTokens();
        sessionStorage.removeItem("foodie_user");
        window.location.href = "login.html";
    }
});

// Update Profile
const profileForm = document.getElementById("profileForm");

if (profileForm) {
    profileForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const userData = {
            username: document.getElementById("username").value.trim(),
            full_name: document.getElementById("full_name").value.trim(),
            email: document.getElementById("email").value.trim(),
            phone: document.getElementById("phone").value.trim() || null
        };

        const button = profileForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.textContent = "Updating...";

        try {
            const response = await API.patch(
                FOODIE_CONFIG.ENDPOINTS.PROFILE,
                userData
            );

            showProfileMessage(
                "Profile updated successfully.",
                "success"
            );

            sessionStorage.setItem("foodie_user", JSON.stringify(response));

        } catch (error) {
            showProfileMessage(error.message, "error");
        } finally {
            button.disabled = false;
            button.textContent = "Update Profile";
        }
    });
}

function showProfileMessage(message, type) {
    const element = document.getElementById("profileMessage");
    element.textContent = message;
    element.className = `message ${type}`;
}

// Logout
const logoutButton = document.getElementById("logoutButton");

if (logoutButton) {
    logoutButton.addEventListener("click", async function (event) {
        event.preventDefault();

        try {
            await API.post(FOODIE_CONFIG.ENDPOINTS.LOGOUT, {});
        } catch (error) {
            console.error(error.message);
        } finally {
            API.clearTokens();
            sessionStorage.removeItem("foodie_user");
            window.location.href = "login.html";
        }
    });
}
