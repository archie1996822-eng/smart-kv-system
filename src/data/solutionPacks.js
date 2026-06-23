export const solutionPacks = [
  {
    id: 'product-launch',
    name: '新品发布会',
    icon: 'rocket_launch',
    desc: '科技产品 / 品牌发布',
    materials: ['hand-sign', 'flag', 'badge', 'stand', 'welcome-board', 'host-card'],
  },
  {
    id: 'annual-gala',
    name: '年会盛典',
    icon: 'celebration',
    desc: '企业年会 / 颁奖典礼',
    materials: ['hand-sign', 'flag', 'badge', 'ticket', 'signboard', 'host-card'],
  },
  {
    id: 'store-opening',
    name: '门店开业',
    icon: 'storefront',
    desc: '餐饮 / 零售门店',
    materials: ['hand-sign', 'flag', 'canvas-bag', 'paper-bag', 'ticket', 'signboard'],
  },
  {
    id: 'summit-forum',
    name: '峰会论坛',
    icon: 'groups',
    desc: '行业峰会 / 论坛',
    materials: ['flag', 'badge', 'stand', 'badge-sticker', 'manual', 'welcome-board'],
  },
  {
    id: 'exhibition',
    name: '展览展示',
    icon: 'museum',
    desc: '展会 / 美术馆',
    materials: ['stand', 'flag', 'canvas-bag', 'badge', 'signboard', 'badge-sticker'],
  },
  {
    id: 'sports-event',
    name: '运动赛事',
    icon: 'sports_soccer',
    desc: '马拉松 / 运动会',
    materials: ['flag', 'badge', 'hand-sign', 'ticket', 'canvas-bag', 'signboard'],
  },
];

export function getPackById(id) {
  return solutionPacks.find(p => p.id === id) || null;
}
