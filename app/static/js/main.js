async function toggleFavorite(event, btn, productId) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/favorites/${productId}`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to update favorite");
        }

        const data = await response.json();

        const heartIcon = btn.querySelector(".material-symbols-outlined");

        heartIcon.classList.toggle("filled", data.is_favorite);

        const actionText = data.is_favorite
            ? "Remove from favorites"
            : "Add to favorites";

        btn.setAttribute("title", actionText);
        btn.setAttribute("aria-label", actionText);

    } catch (error) {
        console.error("Could not update favorite:", error);
    }
}

async function signup(event, btn, full_name, email, password, repeat_password) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/users/${email}`, {
            method: "POST",
            body: JSON.stringify({
                full_name: full_name,
                email: email,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error("Failed to sign up user");
        }

    } catch (error) {
        console.error("Could not sign up user:", error);
    }
}

async function login(event, btn, email, password) {
    event.stopPropagation();

    try {
        const response = await fetch(`/api/users/${email}`, {
            method: "GET",
        });

        if (!response.ok) {
            throw new Error("Failed to get user");
        }

        const data = await response.json();
    }
}