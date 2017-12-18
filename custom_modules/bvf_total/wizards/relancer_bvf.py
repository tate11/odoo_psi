# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime

from odoo import api, models, fields, SUPERUSER_ID


class relancer_bvf(models.TransientModel):
    _name = "relancer.bvf"
    
    def _default_bvf_ids(self):
        return self.env['bvf.total'].search([('state','!=','payee')]).ids
        #return self._context.get('active_ids')
        
    direction_id = fields.Many2one(string='Direction', comodel_name='direction.total')
    service_id = fields.Many2one(string='Service', comodel_name='service.total')
    utilisateur_id = fields.Many2one(string='Utilisateur', comodel_name='res.users')
    utilisateur_ids = fields.Many2many(string='Utilisateurs destinataires', comodel_name='res.users')
    bvf_ids = fields.Many2many(string='BVFs', comodel_name='bvf.total', default=_default_bvf_ids)
    commentaire = fields.Text(string='Commentaire', size = 200)
    
    @api.onchange('direction_id')                
    def onchange_direction(self):
        res = {}
        if self.direction_id:
            self.service_id = False
            res['domain'] = {'service_id':[('direction_id','=',self.direction_id.id)], 'utilisateur_id':[('direction_id','=',self.direction_id.id)]}
            self.utilisateur_ids = self.env['res.users'].search([('direction_id','=',self.direction_id.id)])            
        return res
    
    @api.onchange('service_id')                
    def onchange_service(self):
        res = {}
        if self.service_id:
            self.utilisateur_id = False
            res['domain'] = {'utilisateur_id':[('service_id','=',self.service_id.id)]}
            self.utilisateur_ids = self.env['res.users'].search([('service_id','=',self.service_id.id)])
        else:
            self.onchange_direction()
        return res
    
    @api.onchange('utilisateur_ids')                
    def onchange_utilisateurs(self):
        list_users_meme_profil = self.env['res.users'].ids 
        
        # CHOIX MULTIPLE DE L'UTILISATEUR
        """for utilisateur in self.utilisateur_ids:
            group_compta_treso = self.env['res.groups'].search([('id','in',[self.env.ref('bvf_total.group_comptables').id, self.env.ref('bvf_total.group_tresoriers').id])])
            for group in group_compta_treso:
                if utilisateur in group.users:
                    list_users_meme_profil += group.users.ids 
                    
            # self.utilisateur_id est agent admin ou prescripteur        
            group_agent_prescr = self.env['res.groups'].search([('id','in',[self.env.ref('bvf_total.group_agent_administratif').id, self.env.ref('bvf_total.group_prescripteur').id])])           
            if utilisateur in group_agent_prescr.mapped('users'):
                list_users_meme_profil = [self.utilisateur_id.id]
                    
            self.utilisateur_ids = list_users_meme_profil"""
        
        # CHOIX UNIQUE DE L'UTILISATEUR
        if self.utilisateur_id:
             # self.utilisateur_id est comptable na treso
            group_compta_treso = self.env['res.groups'].search([('id','in',[self.env.ref('bvf_total.group_comptables').id, self.env.ref('bvf_total.group_tresoriers').id])])
            for group in group_compta_treso:
                if self.utilisateur_id in group.users:
                    list_users_meme_profil += group.users.ids 
                    
            # self.utilisateur_id est agent admin ou prescripteur        
            group_agent_prescr = self.env['res.groups'].search([('id','in',[self.env.ref('bvf_total.group_agent_administratif').id, self.env.ref('bvf_total.group_prescripteur').id])])           
            if self.utilisateur_id in group_agent_prescr.mapped('users'):
                list_users_meme_profil = [self.utilisateur_id.id]
                    
            self.utilisateur_ids = list_users_meme_profil
        else:
            self.onchange_service()
            
        # CHECKER LE PROFIL DE L'UTILISATEUR DESTINATAIRE ET FILTRER LES BVFS        
        
    def relance_bvf_old(self, bvf_ids_list):
        normal_ids = []
        urgent_ids = []
        tres_urgent_ids = []
        
        for bvf in bvf_ids_list:
            if(bvf.statut_label == 'Normal'):
                normal_ids.append(bvf.id)
            elif(bvf.statut_label == 'Urgent'):
                urgent_ids.append(bvf.id)
            elif(bvf.statut_label == u'Très urgent'):
                tres_urgent_ids.append(bvf.id)
        
        # recuperer les utilisateurs de même direction, ou même service ou même profil avec la selection 
            
        emails_to =  []
        emails_to_str = ""
        
        # si on a selectionnee une direction, service, utilisateur        
        for utilisateur in self.utilisateur_ids:
            if utilisateur.partner_id.email:
                emails_to.append(utilisateur.partner_id.email)                
                
        emails_to_str = str(','.join(emails_to))        
        print 'emails_to_str'
        #print emails_to
        print emails_to_str
                
        if normal_ids:
            template_normal = self.env.ref('bvf_total.relancer_normal_bvf', False)
            template_normal.email_to = emails_to_str
            #print template_normal.email_to
            template_normal.with_context(bvf_ids=normal_ids).send_mail(self.id, force_send=True, raise_exception=True)

            
        if urgent_ids:
            template_urgent = self.env.ref('bvf_total.relancer_urgent_bvf', False)
            template_urgent.email_to = emails_to_str
            template_urgent.with_context(bvf_ids=urgent_ids).send_mail(self.id, force_send=True, raise_exception=True)
            
        if tres_urgent_ids:
            template_tres_urgent = self.env.ref('bvf_total.relancer_tres_urgent_bvf', False)
            template_tres_urgent.email_to = emails_to_str
            template_tres_urgent.with_context(bvf_ids=tres_urgent_ids).send_mail(self.id, force_send=True, raise_exception=True)
            
    def relance_bvf(self, bvf_ids_list, mail_destinataire):
        
        mail_destinataire = mail_destinataire + ", haingovalimbavaka@gmail.com"        
        # repartition des bvfs selon l'urgence
        normal_ids = []
        urgent_ids = []
        tres_urgent_ids = []
        
        for bvf in bvf_ids_list:
            if(bvf.statut_label == 'Normal'):
                normal_ids.append(bvf.id)
            elif(bvf.statut_label == 'Urgent'):
                urgent_ids.append(bvf.id)
            elif(bvf.statut_label == u'Très urgent'):
                tres_urgent_ids.append(bvf.id)
        
        print 'stat bvfs -----------------'        
        print normal_ids
        print urgent_ids
        print tres_urgent_ids
                
        if normal_ids:
            template_normal = self.env.ref('bvf_total.relancer_normal_bvf', False)
            template_normal.email_to = mail_destinataire
            template_normal.with_context(bvf_ids=normal_ids).send_mail(self.id, force_send=True, raise_exception=True)

            
        if urgent_ids:
            template_urgent = self.env.ref('bvf_total.relancer_urgent_bvf', False)
            template_urgent.email_to = mail_destinataire
            template_urgent.with_context(bvf_ids=urgent_ids).send_mail(self.id, force_send=True, raise_exception=True)
            
        if tres_urgent_ids:
            template_tres_urgent = self.env.ref('bvf_total.relancer_tres_urgent_bvf', False)
            template_tres_urgent.email_to = mail_destinataire
            template_tres_urgent.with_context(bvf_ids=tres_urgent_ids).send_mail(self.id, force_send=True, raise_exception=True)
            
    @api.multi
    def relancer_bvf_action(self):
        # PARCOURIR LES DESTINATAIRES ET FILTRER LES BVFs RATTACHEES        
        # si on a selectionnee une direction, service, utilisateur     
        # definir le profil pour voir les bvfs à relancer
        
        for utilisateur in self.utilisateur_ids:
            print 'bvfs 1 : '
            print self.bvf_ids.ids
            
            group_treso = self.env['res.groups'].search([('id','=',self.env.ref('bvf_total.group_tresoriers').id)])
            for group in group_treso:
                if utilisateur in group.users:
                    self.bvf_ids = self.env['bvf.total'].search([('state','in',['recu_treso', 'ok_paimt_immediat', 'bon_a_payer'])])  
                    
            group_compta = self.env['res.groups'].search([('id','=',self.env.ref('bvf_total.group_comptables').id)])
            for group in group_compta:
                if utilisateur in group.users:
                    self.bvf_ids = self.env['bvf.total'].search([('state','in',['ok_paimt_normal', 'refacturer', 'compta_gen_nd'])])  
                    
            # self.utilisateur_id est agent admin ou prescripteur        
            group_agent_adm = self.env['res.groups'].search([('id','=',self.env.ref('bvf_total.group_agent_administratif').id)])           
            if utilisateur in group_agent_adm.mapped('users'):
                self.bvf_ids = self.env['bvf.total'].search([('state','=','recu_verifiee'), ('responsable_id','=',utilisateur.id)]) 
                
            group_prescr = self.env['res.groups'].search([('id','=',self.env.ref('bvf_total.group_prescripteur').id)])           
            if utilisateur in group_prescr.mapped('users'):
                self.bvf_ids = self.env['bvf.total'].search([('state','=','envoi_presc'), ('responsable_id','=',utilisateur.id)]) 
                                  
        for utilisateur in self.utilisateur_ids:
            if utilisateur.partner_id.email:
                print 'mail'
                print utilisateur.partner_id.email
                print 'bvfs 2 :'
                print self.bvf_ids.ids
                
                self.relance_bvf(self.bvf_ids, utilisateur.partner_id.email) 
                #emails_to.append(utilisateur.partner_id.email)                
                
        #emails_to_str = str(','.join(emails_to))        
        #print 'emails_to_str'
        #print emails_to_str
            
    def modif_status_bvf(self):     
        # recherche de la liste des bvfs non payées
        bvf_ids_list = self.env['bvf.total'].search([('state','!=','payee')])  
        for record in bvf_ids_list:            
            #diff_day = record.echeance - datetime.date      
            date_format = "%Y-%m-%d"
            a = datetime.strptime(record.echeance, date_format)
            b = datetime.strptime(date.today().strftime('%Y-%m-%d'), date_format)
            diff_day = abs((b - a).days)
            if (diff_day <=7):
                record.statut_label = 'Très urgent'
            else:
                if(diff_day <=15):
                    record.statut_label = 'Urgent'
                else:
                    record.statut_label = 'Normal'
        
    # 7h00 tous les jours: relance urgent, tres urgent et modif status    
    @api.model
    def _cron_7h00(self):     
        # relancer les bvfs non payés
        bvf_ids_list = self.env['bvf.total'].search([('statut_label','!=','Normal'),('state','!=','payee')])
        super_user = self.env['res.users'].browse(SUPERUSER_ID)
        relance_id = self.create({'direction_id':super_user.direction_id.id, 
                                  'service_id':super_user.service_id.id,
                                  'utilisateur_id':super_user.id,
                                  'bvf_ids':bvf_ids_list.ids
                                  })   
        # la relance par relance_bvf se fait deja par statut_label
        relance_id.relance_bvf(bvf_ids_list, "haingovalimbavaka@gmail.com")     # TODO
        # mettre a jour les status à 7h00 
        self.modif_status_bvf()       
    
    # 7h00 chaque semaine : relance normal
    @api.model
    def _cron_bvf_normal(self):     
        # recherche de la liste des bvfs à relancer
        bvf_ids_list = self.env['bvf.total'].search([('statut_label','=','Normal'), ('state','!=','payee')])
        super_user = self.env['res.users'].browse(SUPERUSER_ID)
        relance_id = self.create({'direction_id':super_user.direction_id.id, 
                                  'service_id':super_user.service_id.id,
                                  'utilisateur_id':super_user.id,
                                  'bvf_ids':bvf_ids_list.ids
                                  })   
        relance_id.relance_bvf(bvf_ids_list, "haingovalimbavaka@gmail.com")   # TODO
        
    # 12h00 et 16h00 chaque jour : relance très urgent 
    @api.model   
    def _cron_tres_urgent_bvf(self):     
        # recherche de la liste des bvfs à relancer
        bvf_ids_list = self.env['bvf.total'].search([('statut_label','=','Très urgent'), ('state','!=','payee')])   
        super_user = self.env['res.users'].browse(SUPERUSER_ID)
        relance_id = self.create({'direction_id':super_user.direction_id.id, 
                                  'service_id':super_user.service_id.id,
                                  'utilisateur_id':super_user.id,
                                  'bvf_ids':bvf_ids_list.ids
                                  })   
        relance_id.relance_bvf(bvf_ids_list, "haingovalimbavaka@gmail.com")        # TODO


        