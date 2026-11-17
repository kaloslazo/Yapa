import { expect, it } from 'vitest';
import { matchPhotoProduct } from './photoMatches';
it('asigna la única papa del pedido y deja ambigua la mezcla',()=>{
 const a={id:'PAPA-AMARILLA',name:'Papa amarilla',unit:'kg'};const b={id:'PAPA-BLANCA',name:'Papa blanca',unit:'kg'};
 expect(matchPhotoProduct('papa',[a])).toBe(a.id);expect(matchPhotoProduct('papa',[a,b])).toBe('');
 expect(matchPhotoProduct('ajo',[a])).toBe('');
});
