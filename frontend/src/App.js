import { Configuration, OpenAIApi } from 'openai';

import FormSection from './components/FormSection';
import AnswerSection from './components/AnswerSection';


import React, {useEffect, useState} from 'react';
import { Hint } from 'react-autocomplete-hint';

import axios from 'axios';
import KeywordSection from './components/KeywordSection';


const App = () => {
	//const api_host = "http://localhost:9000"
	const api_host = "http://44.204.232.212:9000"
	const [storedValues, setStoredValues] = useState([]);
	const [products, setProducts] = useState([]);
	const [keywords, setKeywords] = useState([]);
	const [hintData, setHintData] = useState([])
	const [loading, setLoading] = useState(false);
	const [text, setText] = useState('')
	const [language, setLanguage] = useState('')

	const getData = async () => {
		const res = await axios.get(`${api_host}/getbrand`)
			setHintData(res.data.brands)	
	  }
	
	  useEffect(()=> {
		getData()
	  },[])

	const updateKeywords = (newKeywords) => {
		setKeywords(newKeywords);
	};

	const Loader = () => {
		return (
		  <div className="loader">
			<div className="spinner"></div>
		  </div>
		);
	  };

	  const ProductCard = ({ product }) => {
		return (
		  <div className="card">
			<table>
				{product.map((product, index) => (
				<tr key={index}>
					<td>{product.id}</td>
					<td>{product.productname}</td>
					<td>{product.shortdescription}</td>
					<td>{product.name}</td>
					<td>{product.price}</td>
					<td><img referrerPolicy="no-referrer" src={product.image_link}></img></td>
				</tr>
				))}
			</table>
		  </div>
		);
	  };
	

	const getRecommendation = async (kw, index) => {
		setLoading(true)				
		const response = await axios.post(`${api_host}/selectitems`, { products: products, keyword:kw , index: index, language: language});
		if (response.data.botresponse) {
			setStoredValues([
				{					
					answer: response.data.botresponse,
					english_answer: response.data.english_response
				}					
			]);
			setLoading(false)			
		}		
	}

	const generateResponse = async (newQuestion, setNewQuestion) => {

		try {
			
			setKeywords([])
			setStoredValues([])
			setLoading(true)			
			const response = await axios.post(`${api_host}/similaritems`, { newQuestion, text });
			if (response.data.botresponse) {
				setStoredValues([
					{
						question: newQuestion,
						// answer: response.data.botresponse,
						// english_answer: response.data.english_response
					}					
				]);
				setNewQuestion('');									
			}

			setProducts(response.data.products);
			setLanguage(response.data.language);
			setLoading(false)			
			const k = await axios.post(`${api_host}/getkeywords`, { products: response.data.products, language: response.data.language });
			//const kw = [{'Price':''}, {'Quality':''}]			
			setKeywords([...new Set(k.data.keywords)])
		  } catch (error) {
			console.error(error);
		  }

		
	};

	return (
		<div>
			<div className="header-section">
				<h1 style={{ fontSize: 18 }}>Generative AI Retail Product Recommendations demo powered by Astra Vector Search</h1>
				{storedValues.length < 1 && (
					<p>
						Please type what you looking for
					</p>
				)}
			</div>
			
			<div className="App">
				<p>Know the brand? Try typing if you want</p>
				<br/>
				<div className="form-section">
				<Hint options={hintData} allowTabFill>
					<input className="textarea"
						value={text}
						onChange={(e) => setText(e.target.value)} 
					/>
				</Hint>
				</div>
			</div>

			{loading ? <Loader /> 
			: <div>
			<FormSection generateResponse={generateResponse}/>
			<KeywordSection keywords={keywords} getRecommendation={getRecommendation} />
			{storedValues.length > 0 && <AnswerSection storedValues={storedValues} />}
			
			<ProductCard product={products} /></div>
			}
		

		</div>
	);
};

export default App;