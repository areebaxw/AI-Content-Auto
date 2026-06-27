const platformLabels = {
  twitter: "Twitter",
  linkedin: "LinkedIn",
  telegram: "Telegram",
  email: "Email",
  instagram: "Instagram",
};

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function toggleLoading(visible) {
  document.getElementById("loading")?.classList.toggle("hidden", !visible);
}

function renderPosts(posts, campaignId, savedPosts = []) {
  const results = document.getElementById("results");
  const grid = document.getElementById("results-grid");
  grid.innerHTML = "";
  const savedLookup = savedPosts.reduce((accumulator, post) => {
    if (!accumulator[post.platform]) {
      accumulator[post.platform] = [];
    }
    accumulator[post.platform].push(post);
    return accumulator;
  }, {});

  Object.entries(posts).forEach(([platform, value]) => {
    const items = Array.isArray(value) ? value : [value];
    const group = document.createElement("section");
    group.className = "platform-group";
    group.innerHTML = `<h4>${platformLabels[platform] || platform}</h4>`;

    items.forEach((item, index) => {
      const content = typeof item === "string" ? item : JSON.stringify(item, null, 2);
      const postId = savedLookup[platform]?.[index]?.id ?? `${platform}-${index}`;
      const card = document.createElement("div");
      card.className = "post-card";
      card.innerHTML = `
        <div class="post-meta">
          <strong>${platformLabels[platform] || platform} #${index + 1}</strong>
          <span>${content.length} chars</span>
        </div>
        <textarea data-platform="${platform}" data-index="${index}">${escapeHtml(content)}</textarea>
        <div class="post-actions">
          <button class="secondary-btn" type="button" data-action="save">Save edit</button>
          <button class="secondary-btn" type="button" data-action="post-now">Post now</button>
        </div>
      `;

      const textarea = card.querySelector("textarea");
      card.querySelector('[data-action="save"]').addEventListener("click", async () => {
        const payload = {
          edited_content: textarea.value,
        };
        const response = await fetch(`/api/post/${postId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          alert("Could not save edit.");
        } else {
          alert("Saved.");
        }
      });

      card.querySelector('[data-action="post-now"]').addEventListener("click", async () => {
        const response = await fetch("/api/post-now", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            campaign_id: campaignId,
            post_id: postId,
            platform,
            content: textarea.value,
          }),
        });
        const result = await response.json();
        alert(result.post_url ? `Posted: ${result.post_url}` : result.status || "Completed");
      });

      group.appendChild(card);
    });

    grid.appendChild(group);
  });

  results.classList.remove("hidden");
}

async function handleGenerateSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const content = formData.get("content")?.toString().trim();
  const file = formData.get("file");

  if (!content && !(file instanceof File && file.size > 0)) {
    alert("Please paste content or upload a .txt file.");
    return;
  }

  toggleLoading(true);
  const response = await fetch("/api/generate", {
    method: "POST",
    body: formData,
  });
  toggleLoading(false);

  const data = await response.json();
  if (!response.ok) {
    alert(data.error || "Generation failed.");
    return;
  }

  renderPosts(data.posts, data.campaign_id, data.saved_posts || []);
}

function bindGenerateForm() {
  const form = document.getElementById("generate-form");
  if (form) {
    form.addEventListener("submit", handleGenerateSubmit);
  }
}

function bindSchedulePage() {
  const list = document.getElementById("schedule-post-list");
  const form = document.getElementById("schedule-form");
  const feedback = document.getElementById("schedule-feedback");
  if (!list || !form) return;

  list.addEventListener("click", (event) => {
    const button = event.target.closest(".selectable-post");
    if (!button) return;
    document.querySelectorAll(".selectable-post").forEach((node) => node.classList.remove("active"));
    button.classList.add("active");
    document.getElementById("schedule-post-id").value = button.dataset.postId;
    document.getElementById("schedule-platform").value = button.dataset.platform;
    feedback.textContent = `Selected ${button.dataset.platform} post #${button.dataset.postId}`;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const postId = document.getElementById("schedule-post-id").value;
    const platform = document.getElementById("schedule-platform").value;
    const scheduledTime = document.getElementById("scheduled-time").value;

    if (!postId || !platform || !scheduledTime) {
      feedback.textContent = "Select a post and pick a time.";
      return;
    }

    const response = await fetch("/api/schedule", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ post_id: postId, platform, scheduled_time: new Date(scheduledTime).toISOString() }),
    });
    const data = await response.json();
    feedback.textContent = data.status === "scheduled" ? "Scheduled successfully." : "Scheduling failed.";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindGenerateForm();
  bindSchedulePage();
});
