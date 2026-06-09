import React from 'react';
import SentenceCard from './SentenceCard';
import FactualSidebar from './FactualSidebar';
import BiasFlowChart from './BiasFlowChart';

export default function ArticleReader({ data }) {
  if (!data || !data.sentences || data.sentences.length === 0) return null;

  return (
    <div className="fade-in">
      {/* Bias Flow Chart — shows bias direction across the article */}
      {data.bias_flow && data.bias_flow.length >= 2 && (
        <BiasFlowChart flow={data.bias_flow} />
      )}

      <div className="reader-layout">
        <div className="article-reader glass-card">
          <h2>{data.article_title}</h2>
          <p style={{ lineHeight: 2 }}>
            {data.sentences.map((s, i) => <SentenceCard key={i} sentence={s} />)}
          </p>
        </div>
        <FactualSidebar paragraphs={data.paragraphs} />
      </div>
    </div>
  );
}
