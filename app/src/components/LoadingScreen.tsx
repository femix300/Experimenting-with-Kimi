import { Activity } from "lucide-react";

const LoadingScreen = ({ message = "Loading..." }: { message?: string }) => (
  <div className="flex items-center justify-center min-h-screen bg-[#0a0e17]">
    <div className="text-center">
      <div className="relative w-16 h-16 mx-auto mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-[#1a2030]" />
        <div className="absolute inset-0 rounded-full border-2 border-t-[#00d4ff] border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        <Activity className="absolute inset-0 m-auto w-6 h-6 text-[#00d4ff]" />
      </div>
      <p className="text-[#8b92a8] text-sm">{message}</p>
    </div>
  </div>
);

export default LoadingScreen;