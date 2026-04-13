"use client";

export function YoutubeEmbed({ videoId }: { videoId: string }) {
  return (
    <div className="w-full max-w-5xl mx-auto px-4">
      <div className="relative w-full overflow-hidden rounded-2xl shadow-lg aspect-video">
        <iframe
          src={`https://www.youtube.com/embed/${videoId}?rel=0&modestbranding=1`}
          title="YouTube video player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="absolute top-0 left-0 w-full h-full shadow-lg"
        />
      </div>
    </div>
  );
}
