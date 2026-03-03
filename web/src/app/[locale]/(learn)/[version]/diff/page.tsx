import Link from "next/link";
import { VERSION_META } from "@/lib/constants";
import { getTranslations } from "@/lib/i18n-server";
import { DiffPageContent } from "./diff-content";
import { getVersionServer, getRelatedVersionsServer } from "@/lib/server-api";

interface DiffPageProps {
  params: Promise<{ locale: string; version: string }>;
}

export default async function DiffPage({ params }: DiffPageProps) {
  const { locale, version } = await params;
  const t = getTranslations(locale, "diff");
  
  // 从 API 获取版本数据和相关版本
  const [versionData, relatedData] = await Promise.all([
    getVersionServer(version),
    getRelatedVersionsServer(version),
  ]);

  const meta = VERSION_META[version];

  if (!meta || !versionData) {
    return (
      <div className="py-12 text-center">
        <p className="text-zinc-500">Version not found.</p>
        <Link href={`/${locale}/timeline`} className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Back to timeline
        </Link>
      </div>
    );
  }

  const prevVersion = relatedData.previous;
  const prevMeta = prevVersion ? VERSION_META[prevVersion.id] : null;

  if (!prevVersion) {
    return (
      <div className="py-12">
      <Link
          href={`/${locale}/${version}`}
          className="mb-6 inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
        >
          <span>&larr;</span>
          Back to {meta.title}
        </Link>
        <h1 className="text-3xl font-bold">{meta.title}</h1>
        <p className="mt-4 text-zinc-500">
          This is the first version -- there is no previous version to compare against.
        </p>
      </div>
    );
  }

  return (
    <div className="py-4">
      <Link
        href={`/${locale}/${version}`}
        className="mb-6 inline-flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
      >
        <span>&larr;</span>
        Back to {meta.title}
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          {prevMeta?.title || prevVersion.id} &rarr; {meta.title}
        </h1>
        <p className="mt-2 text-zinc-500 dark:text-zinc-400">
          {prevVersion.id} ({prevVersion.loc} LOC) &rarr; {version} ({versionData.loc} LOC)
        </p>
      </div>

      {/* Diff Content */}
      <DiffPageContent
        version={version}
        prevVersion={prevVersion}
        currentVersion={versionData}
        prevMeta={prevMeta}
        currentMeta={meta}
      />
    </div>
  );
}
