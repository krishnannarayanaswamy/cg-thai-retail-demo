const KeywordSection = ({ keywords, getRecommendation }) => {

    console.log(keywords);

    return (
      <div className="grid-container">
        {keywords.length > 0 ? (
          <div className="grid">
            <h2>What is your criteria?</h2>
            {keywords.map((keyword, index) => (
              <button key={index} className="grid-item" onClick={()=> {getRecommendation(keyword, index)}}>{Object.keys(keyword)[0]}</button>
            ))}
          </div>
        ) : (
          <p></p>
        )}
      </div>
    );
  };

export default KeywordSection