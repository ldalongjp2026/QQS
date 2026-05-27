const form = document.querySelector("#invoice-form");
const statusText = document.querySelector("#status");
const submit = document.querySelector(".submit");

function collectFormData(formElement) {
  const formData = new FormData(formElement);
  return Object.fromEntries(formData.entries());
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusText.textContent = "PDFを生成しています...";
  submit.disabled = true;

  try {
    const payload = collectFormData(form);
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || "PDF生成に失敗しました");
    }

    const pdf = await response.blob();
    const recipient = (payload.recipient || "請求書").replace(/[\\/:*?"<>|\s]+/g, "_");
    downloadBlob(pdf, `QQS_${recipient}.pdf`);
    statusText.textContent = "PDFを生成しました。";
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});
