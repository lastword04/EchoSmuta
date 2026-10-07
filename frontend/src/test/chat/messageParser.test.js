import { describe, it, expect } from 'vitest';
import { parseSmileys, parseMentions, parseUrls, isYouTube } from '../../widgets/BottomPanel/ChatPanel/ChatContent/messageParser';

describe('parseSmileys', () => {
  it('находит смайлик |123| в тексте', () => {
    const result = parseSmileys('Привет |123| мир');
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      index: 7,
      fullMatch: '|123|',
      smileyNumber: '123',
    });
  });

  it('находит несколько смайликов |123| и |456|', () => {
    const result = parseSmileys('start |123| middle |456| end');
    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({ index: 6, fullMatch: '|123|', smileyNumber: '123' });
    expect(result[1]).toMatchObject({ index: 19, fullMatch: '|456|', smileyNumber: '456' });
  });

  it('возвращает пустой массив если смайликов нет', () => {
    expect(parseSmileys('обычный текст без смайликов')).toEqual([]);
    expect(parseSmileys('')).toEqual([]);
  });

  it('находит смайлик в начале текста', () => {
    const result = parseSmileys('|7| привет');
    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ index: 0, fullMatch: '|7|', smileyNumber: '7' });
  });
});

describe('parseMentions', () => {
  it('находит mention [Имя](123) в тексте', () => {
    const result = parseMentions('Привет [Иван](123) как дела');
    expect(result).toHaveLength(1);
    expect(result[0]).toEqual({
      index: 7,
      fullMatch: '[Иван](123)',
      name: 'Иван',
      id: '123',
    });
  });

  it('находит несколько mentions', () => {
    const result = parseMentions('start [Anna](1) middle [Bob](2) end');
    expect(result).toHaveLength(2);
    expect(result[0]).toMatchObject({ name: 'Anna', id: '1', fullMatch: '[Anna](1)' });
    expect(result[1]).toMatchObject({ name: 'Bob', id: '2', fullMatch: '[Bob](2)' });
  });

  it('возвращает пустой массив если mentions нет', () => {
    expect(parseMentions('текст без упоминаний')).toEqual([]);
    // неполный синтаксис не является mention
    expect(parseMentions('[Имя] без скобок (123)')).toEqual([]);
  });

  it('находит mention в начале текста', () => {
    const result = parseMentions('[Имя](42) текст');
    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ index: 0, name: 'Имя', id: '42' });
  });
});

describe('parseUrls', () => {
  it('находит https://example.com', () => {
    const result = parseUrls('смотри https://example.com тут');
    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ url: 'https://example.com' });
    expect(result[0].index).toBe(7);
  });

  it('находит www.example.com', () => {
    const result = parseUrls('ссылка www.example.com конец');
    expect(result).toHaveLength(1);
    expect(result[0].url).toBe('www.example.com');
  });

  it('находит несколько URL', () => {
    const result = parseUrls('https://a.com и www.b.org и c.net');
    expect(result).toHaveLength(3);
    expect(result.map((m) => m.url)).toEqual([
      'https://a.com',
      'www.b.org',
      'c.net',
    ]);
  });

  it('возвращает пустой массив если URL нет', () => {
    expect(parseUrls('просто текст без ссылок')).toEqual([]);
    expect(parseUrls('')).toEqual([]);
  });

  it('захватывает путь после домена', () => {
    const result = parseUrls('https://example.com/path/to?page=1');
    expect(result).toHaveLength(1);
    expect(result[0].url).toBe('https://example.com/path/to?page=1');
  });
});

describe('isYouTube', () => {
  it('возвращает true для youtube.com', () => {
    expect(isYouTube('youtube.com')).toBe(true);
    expect(isYouTube('https://youtube.com/watch?v=abc')).toBe(true);
    expect(isYouTube('https://www.youtube.com/watch?v=abc')).toBe(true);
  });

  it('возвращает true для youtu.be', () => {
    expect(isYouTube('youtu.be')).toBe(true);
    expect(isYouTube('https://youtu.be/abc123')).toBe(true);
  });

  it('возвращает true для m.youtube.com (поддомен)', () => {
    expect(isYouTube('m.youtube.com')).toBe(true);
    expect(isYouTube('https://m.youtube.com/watch?v=abc')).toBe(true);
  });

  it('возвращает false для example.com', () => {
    expect(isYouTube('example.com')).toBe(false);
    expect(isYouTube('https://example.com')).toBe(false);
  });

  it('возвращает false для невалидного URL', () => {
    expect(isYouTube('')).toBe(false);
    expect(isYouTube('not a url')).toBe(false);
  });

  it('не путает поддомены с частью домена (fakeyoutube.com)', () => {
    // host 'fakeyoutube.com' не оканчивается на '.youtube.com' и не равен 'youtube.com'
    expect(isYouTube('fakeyoutube.com')).toBe(false);
  });
});