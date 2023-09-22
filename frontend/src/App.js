import { Configuration, OpenAIApi } from 'openai';

import FormSection from './components/FormSection';
import AnswerSection from './components/AnswerSection';

import React, {useEffect, useState} from 'react';
import { Hint } from 'react-autocomplete-hint';
import Iframe from 'react-iframe'
import axios from 'axios';


const App = () => {

	const [storedValues, setStoredValues] = useState([]);
	const [products, setProducts] = useState([]);
	const [hintData, setHintData] = useState([])
	const [text, setText] = useState('')

	const getData = async () => {
		const res = await axios.get('http://44.204.232.212:9000/getbrand')
			setHintData(res.data.brands)	
	  }
	
	  useEffect(()=> {
		getData()
	  },[])

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
	

	const generateResponse = async (newQuestion, setNewQuestion) => {

		try {
			const response = await axios.post('http://44.204.232.212:9000/similaritems', { newQuestion, text });
			if (response.data.botresponse) {
				setStoredValues([
					{
						question: newQuestion,
						answer: response.data.botresponse,
					},
					...storedValues,
				]);
				setNewQuestion('');	
			}

			setProducts(response.data.products);
			setText('')
			
		  } catch (error) {
			console.error(error);
		  }

		
	};

	return (
		<div>
			<div className="header-section">
				<h1 style={{ fontSize: 18 }}>Generative AI Retail Product Recommendations demo powered by Astra VectorDB</h1>
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

			<FormSection generateResponse={generateResponse} />

			{storedValues.length > 0 && <AnswerSection storedValues={storedValues} />}

			<ProductCard product={products} />
		

		
		</div>


	);
};

export default App;