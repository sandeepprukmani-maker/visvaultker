import BrowserPreview from "../BrowserPreview";

export default function BrowserPreviewExample() {
  return (
    <div className="h-96">
      <BrowserPreview
        isLoading={false}
        currentUrl="https://example.com"
      />
    </div>
  );
}
