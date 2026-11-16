
// FoodieExpress Dashboard

document.addEventListener("DOMContentLoaded", async function () {
    const accessToken = API.getAccessToken();

    if (!accessToken) {
        window.location.href = "login.html";
        return;
    }

    try {
        // Verify the session with the backend.
        const user = await API.get(FOODIE_CONFIG.ENDPOINTS.PROFILE);

        sessionStorage.setItem("foodie_user", JSON.stringify(user));

        document.getElementById("userName").textContent =
            user.full_name || "Not available";

        document.getElementById("userEmail").textContent =
            user.email || "Not available";

        document.getElementById("userUsername").textContent =
            user.username || "Not available";

        // Convert role ID into role name.
        const roleNames = {
            1: "CUSTOMER",
            2: "RESTAURANT_OWNER",
            3: "DELIVERY_PARTNER",
            4: "ADMIN"
        };

        document.getElementById("userRole").textContent =
            roleNames[user.role_id] || "Unknown";

        // Show restaurant options only to Restaurant Owners.
        const isRestaurantOwner = Number(user.role_id) === 2;

        const restaurantLinks = document.querySelectorAll(
            'a[href="pages/restaurant-register.html"], ' +
            'a[href="pages/restaurant-management.html"]'
        );

        restaurantLinks.forEach(link => {
            link.style.display = isRestaurantOwner ? "" : "none";

            const card = link.closest(".card");

            if (card) {
                card.style.display = isRestaurantOwner ? "" : "none";
            }
        });

    } catch (error) {
        console.error("Dashboard error:", error.message);

        API.clearTokens();
        sessionStorage.removeItem("foodie_user");
        window.location.href = "login.html";
    }
});

// Logout
const logoutButton = document.getElementById("logoutButton");

if (logoutButton) {
    logoutButton.addEventListener("click", async function (event) {
        event.preventDefault();

        try {
            await API.post(FOODIE_CONFIG.ENDPOINTS.LOGOUT, {});
        } catch (error) {
            console.error("Logout error:", error.message);
        } finally {
            API.clearTokens();
            sessionStorage.removeItem("foodie_user");
            window.location.href = "login.html";
        }
    });
}
