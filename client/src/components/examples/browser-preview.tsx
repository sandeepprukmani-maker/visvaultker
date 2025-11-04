import { BrowserPreview } from "../browser-preview";

export default function BrowserPreviewExample() {
  return (
    <div className="h-96 p-4">
      <BrowserPreview url="https://linkedin.com/in/johndoe" isLoading={true} />
    </div>
  );
}
