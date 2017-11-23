package hocon

import (
	"os"
	"strings"
)

type IncludeCallback func(filename string) *HoconRoot

type Parser struct {
	reader   *HoconTokenizer
	root     *HoconValue
	callback IncludeCallback

	substitutions []*HoconSubstitution
}

func Parse(text string, callback IncludeCallback) *HoconRoot {
	return new(Parser).parseText(text, callback)
}

func (p *Parser) parseText(text string, callback IncludeCallback) *HoconRoot {
	p.callback = callback
	p.root = NewHoconValue()
	p.reader = NewHoconTokenizer(text)
	p.reader.PullWhitespaceAndComments()
	p.parseObject(p.root, true, "")

	root := NewHoconRoot(p.root)

	cRoot := root.Value()

	for _, sub := range p.substitutions {
		res := getNode(cRoot, sub.Path)
		if res == nil {
			envVal, exist := os.LookupEnv(sub.Path)
			if !exist {
				if !sub.IsOptional {
					panic("Unresolved substitution:" + sub.Path)
				}
			} else {
				hv := NewHoconValue()
				hv.AppendValue(NewHoconLiteral(envVal))
				sub.ResolvedValue = hv
			}
		} else {
			sub.ResolvedValue = res
		}
	}

	return NewHoconRoot(p.root, p.substitutions...)
}

func (p *Parser) parseObject(owner *HoconValue, root bool, currentPath string) {
	if !owner.IsObject() {
		owner.NewValue(NewHoconObject())
	}

	if owner.IsObject() {
		rootObj := owner
		for rootObj.oldValue != nil {
			oldObj := rootObj.oldValue.GetObject()
			obj := rootObj.GetObject()

			if oldObj == nil || obj == nil {
				break
			}
			obj.Merge(oldObj)
			rootObj = rootObj.oldValue
		}
	}

	currentObject := owner.GetObject()

	for !p.reader.EOF() {
		t := p.reader.PullNext()

		switch t.tokenType {
		case TokenTypeInclude:
			included := p.callback(t.value)
			substitutions := included.substitutions
			for _, substitution := range substitutions {
				substitution.Path = currentPath + "." + substitution.Path
			}
			p.substitutions = append(p.substitutions, substitutions...)
			otherObj := included.value.GetObject()
			owner.GetObject().Merge(otherObj)
		case TokenTypeEoF:
		case TokenTypeKey:
			value := currentObject.GetOrCreateKey(t.value)
			nextPath := t.value
			if len(currentPath) > 0 {
				nextPath = currentPath + "." + t.value
			}
			p.parseKeyContent(value, nextPath)
			if !root {
				return
			}
		case TokenTypeObjectEnd:
			return
		}
	}
}

func (p *Parser) parseKeyContent(value *HoconValue, currentPath string) {
	for !p.reader.EOF() {
		t := p.reader.PullNext()
		switch t.tokenType {
		case TokenTypeDot:
			p.parseObject(value, false, currentPath)
			return
		case TokenTypeAssign:
			{
				if !value.IsObject() {
					value.Clear()
				}
			}
			p.ParseValue(value, false, currentPath)
			return
		case TokenTypePlusAssign:
			{
				if !value.IsObject() {
					value.Clear()
				}
			}
			p.ParseValue(value, true, currentPath)
			return
		case TokenTypeObjectStart:
			p.parseObject(value, true, currentPath)
			return
		}
	}
}

func (p *Parser) ParseValue(owner *HoconValue, isEqualPlus bool, currentPath string) {
	if p.reader.EOF() {
		panic("End of file reached while trying to read a value")
	}

	p.reader.PullWhitespaceAndComments()
	for p.reader.isValue() {
		t := p.reader.PullValue()

		if isEqualPlus {
			sub := p.ParseSubstitution(currentPath, false)
			p.substitutions = append(p.substitutions, sub)
			owner.AppendValue(sub)
		}

		switch t.tokenType {
		case TokenTypeEoF:
		case TokenTypeLiteralValue:
			if owner.IsObject() {
				owner.Clear()
			}
			lit := NewHoconLiteral(t.value)
			owner.AppendValue(lit)
		case TokenTypeObjectStart:
			p.parseObject(owner, true, currentPath)
		case TokenTypeArrayStart:
			arr := p.ParseArray(currentPath)
			owner.AppendValue(&arr)
		case TokenTypeSubstitute:
			sub := p.ParseSubstitution(t.value, t.isOptional)
			p.substitutions = append(p.substitutions, sub)
			owner.AppendValue(sub)
		}

		if p.reader.IsSpaceOrTab() {
			p.ParseTrailingWhitespace(owner)
		}
	}
	p.ignoreComma()
	p.ignoreNewline()
}

func (p *Parser) ParseTrailingWhitespace(owner *HoconValue) {
	ws := p.reader.PullSpaceOrTab()
	if len(ws.value) > 0 {
		wsList := NewHoconLiteral(ws.value)
		owner.AppendValue(wsList)
	}
}

func (p *Parser) ParseSubstitution(value string, isOptional bool) *HoconSubstitution {
	return NewHoconSubstitution(value, isOptional)
}

func (p *Parser) ParseArray(currentPath string) HoconArray {
	arr := NewHoconArray()
	for !p.reader.EOF() && !p.reader.IsArrayEnd() {
		v := NewHoconValue()
		p.ParseValue(v, false, currentPath)
		arr.values = append(arr.values, v)
		p.reader.PullWhitespaceAndComments()
	}
	p.reader.PullArrayEnd()
	return *arr
}

func (p *Parser) ignoreComma() {
	if p.reader.IsComma() {
		p.reader.PullComma()
	}
}

func (p *Parser) ignoreNewline() {
	if p.reader.IsNewline() {
		p.reader.PullNewline()
	}
}

func getNode(root *HoconValue, path string) *HoconValue {
	elements := splitDottedPathHonouringQuotes(path)
	currentNode := root

	if currentNode == nil {
		panic("Current node should not be null")
	}

	for _, key := range elements {
		currentNode = currentNode.GetChildObject(key)
		if currentNode == nil {
			return nil
		}
	}
	return currentNode
}

func splitDottedPathHonouringQuotes(path string) []string {
	tmp1 := strings.Split(path, "\"")
	var values []string
	for i := 0; i < len(tmp1); i++ {
		tmp2 := strings.Split(tmp1[i], ".")
		for j := 0; j < len(tmp2); j++ {
			if len(tmp2[j]) > 0 {
				values = append(values, tmp2[j])
			}
		}
	}
	return values
}
